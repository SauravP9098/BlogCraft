from __future__ import annotations

import logging
import psycopg
from backend.config import DATABASE_URL

logger = logging.getLogger(__name__)


def init_db():
    """Ensure the generations table exists."""
    if not DATABASE_URL:
        return

    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS blog_generations (
                        id SERIAL PRIMARY KEY,
                        topic TEXT NOT NULL,
                        title TEXT,
                        mode VARCHAR(50),
                        needs_research BOOLEAN DEFAULT FALSE,
                        s3_markdown_url TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )
                conn.commit()
    except Exception as e:
        logger.warning(f"[PostgreSQL] Failed to initialize table: {e}")


def save_generation_record(
    topic: str,
    title: str,
    mode: str,
    needs_research: bool,
    s3_markdown_url: str | None = None,
) -> int | None:
    """Insert a completed generation record into PostgreSQL."""
    if not DATABASE_URL:
        return None

    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO blog_generations (topic, title, mode, needs_research, s3_markdown_url)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (topic, title, mode, needs_research, s3_markdown_url),
                )
                new_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"[PostgreSQL] Saved blog generation #{new_id}")
                return new_id
    except Exception as e:
        logger.warning(f"[PostgreSQL] Failed to save generation record: {e}")
        return None
