from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
BLOGS_DIR = OUTPUTS_DIR / "blogs"
IMAGES_DIR = OUTPUTS_DIR / "images"

# Markdown image links are written relative to the saved .md file
# (outputs/blogs/<slug>.md -> ../images/<file>).
IMAGE_MD_PREFIX = "../images"

# LLM
MODEL_NAME = "gpt-4.1-mini"

# Image generation
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
MAX_IMAGES = 3

# Research
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
