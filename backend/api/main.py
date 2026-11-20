from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import (
    IMAGES_DIR,
    PROJECT_ROOT,
    S3_BUCKET_NAME,
    S3_PUBLIC_BASE_URL,
)
from backend.graph.main_graph import app as blog_graph
from backend.tools.postgres_db import init_db, save_generation_record
from backend.utils.files import _safe_slug, ensure_output_dirs

api = FastAPI(title="BlogCraft — Autonomous Multi-Agent API")

# Initialize database schema on startup
init_db()

# Open CORS so frontend can call the API smoothly
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateRequest(BaseModel):
    topic: str = Field(..., min_length=3)
    as_of: Optional[str] = Field(None, description="ISO date YYYY-MM-DD. Defaults to today.")


class GenerateResponse(BaseModel):
    title: str
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[dict]
    markdown: str
    s3_url: Optional[str] = None


@api.get("/health")
def health() -> dict:
    return {"status": "ok", "engine": "LangGraph + AWS Bedrock"}


@api.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    as_of = req.as_of or date.today().isoformat()
    try:
        date.fromisoformat(as_of)
    except ValueError:
        raise HTTPException(status_code=422, detail="as_of must be YYYY-MM-DD")

    try:
        result = blog_graph.invoke(
            {
                "topic": req.topic,
                "as_of": as_of,
                "sections": [],
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    plan = result.get("plan")
    title = plan.blog_title if plan else req.topic
    mode = result.get("mode", "")
    needs_research = bool(result.get("needs_research"))
    final_md = result.get("final", "")

    s3_url = None
    if S3_BUCKET_NAME:
        s3_url = f"{S3_PUBLIC_BASE_URL}/blogs/{_safe_slug(title)}.md"

    # Persist job metadata in PostgreSQL on Render
    try:
        save_generation_record(
            topic=req.topic,
            title=title,
            mode=mode,
            needs_research=needs_research,
            s3_markdown_url=s3_url,
        )
    except Exception:
        pass

    return GenerateResponse(
        title=title,
        mode=mode,
        needs_research=needs_research,
        queries=result.get("queries", []) or [],
        evidence=[e.model_dump() for e in result.get("evidence", []) or []],
        markdown=final_md,
        s3_url=s3_url,
    )


# Ensure output directories exist and mount static assets
ensure_output_dirs()

if IMAGES_DIR.exists():
    api.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    api.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
