from __future__ import annotations

import re
from pathlib import Path

from backend.config import BLOGS_DIR, IMAGES_DIR


def _safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"


def ensure_output_dirs() -> None:
    BLOGS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def save_markdown(blog_title: str, md: str) -> Path:
    """Write the final markdown to outputs/blogs/<slug>.md and return the path."""
    ensure_output_dirs()
    path = BLOGS_DIR / f"{_safe_slug(blog_title)}.md"
    path.write_text(md, encoding="utf-8")
    return path
