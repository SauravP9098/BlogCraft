from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.config import IMAGES_DIR, PROJECT_ROOT
from backend.graph.main_graph import app as blog_graph
from backend.utils.files import ensure_output_dirs

api = FastAPI(title="Blog Writing Agent API")

# Open CORS so a separate frontend (frontend/index.html) can call the API.
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


@api.get("/health")
def health() -> dict:
    return {"status": "ok"}


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
    return GenerateResponse(
        title=plan.blog_title if plan else req.topic,
        mode=result.get("mode", ""),
        needs_research=bool(result.get("needs_research")),
        queries=result.get("queries", []) or [],
        evidence=[e.model_dump() for e in result.get("evidence", []) or []],
        markdown=result.get("final", ""),
    )


# Ensure output directories exist and mount static assets
ensure_output_dirs()

if IMAGES_DIR.exists():
    api.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    api.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
