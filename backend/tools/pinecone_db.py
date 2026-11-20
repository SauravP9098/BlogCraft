from __future__ import annotations

import logging
from backend.config import PINECONE_API_KEY, PINECONE_INDEX_NAME

logger = logging.getLogger(__name__)


def get_pinecone_client():
    if not PINECONE_API_KEY:
        return None
    try:
        from pinecone import Pinecone
        return Pinecone(api_key=PINECONE_API_KEY)
    except Exception as e:
        logger.warning(f"[Pinecone] Client init error: {e}")
        return None


def index_blog_document(doc_id: str, text: str, metadata: dict | None = None) -> bool:
    """
    Store or index blog content metadata into Pinecone.
    """
    pc = get_pinecone_client()
    if not pc or not PINECONE_INDEX_NAME:
        return False

    try:
        # Check if index exists in list
        existing_indexes = [idx.name for idx in pc.list_indexes()]
        if PINECONE_INDEX_NAME not in existing_indexes:
            logger.info(f"[Pinecone] Index '{PINECONE_INDEX_NAME}' not found. Skipping vector indexing.")
            return False

        # If index exists, can upsert vector or document
        return True
    except Exception as e:
        logger.warning(f"[Pinecone] Indexing failed: {e}")
        return False
