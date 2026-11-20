from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
BLOGS_DIR = OUTPUTS_DIR / "blogs"
IMAGES_DIR = OUTPUTS_DIR / "images"

# Load .env file reliably from project root or environment
load_dotenv(PROJECT_ROOT / ".env")
load_dotenv()

# Markdown image links relative prefix (for local filesystem fallback)
IMAGE_MD_PREFIX = "../images"

# AWS & Bedrock Configuration
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# Bedrock LLM: supports Anthropic Claude 3.5 / Haiku or Amazon Nova
BEDROCK_CHAT_MODEL = (
    os.getenv("BEDROCK_CHAT_MODEL")
    or os.getenv("BEDROCK_MODEL_ID")
    or "apac.amazon.nova-lite-v1:0"
)

# Bedrock Image Generator
BEDROCK_IMAGE_MODEL = os.getenv("BEDROCK_IMAGE_MODEL", "amazon.nova-2-lite-v1:0")
GEMINI_IMAGE_MODEL = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
MAX_IMAGES = 3

# Amazon S3 Storage
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_REGION = os.getenv("S3_REGION") or AWS_REGION
S3_PUBLIC_BASE_URL = os.getenv("S3_PUBLIC_BASE_URL") or (
    f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com" if S3_BUCKET_NAME else ""
)

# Pinecone Vector Database
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "blogcraft-index")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT") or os.getenv("PINECONE_CLOUD")

# PostgreSQL on Render (handles minor URL typos like sllmode -> sslmode)
raw_db_url = os.getenv("DATABASE_URL", "")
if "sllmode=" in raw_db_url:
    raw_db_url = raw_db_url.replace("sllmode=", "sslmode=")
DATABASE_URL = raw_db_url

# Observability
RIUS_API_KEY = os.getenv("RIUS_API_KEY")

# Web Research (Tavily)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
MAX_QUERIES = 10
MAX_RESULTS_PER_QUERY = 6
ORCH_EVIDENCE_LIMIT = 16
WORKER_EVIDENCE_LIMIT = 20

# Recency window (days) per router mode
RECENCY_DAYS = {
    "open_book": 7,
    "hybrid": 45,
    "closed_book": 3650,
}
