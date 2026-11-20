from __future__ import annotations

import logging
from typing import Any
from langchain_aws import ChatBedrockConverse
from backend.config import (
    AWS_ACCESS_KEY_ID,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    BEDROCK_CHAT_MODEL,
)

logger = logging.getLogger(__name__)

# Log which model is in use at startup
logger.info(f"[Bedrock] Chat model configured: {BEDROCK_CHAT_MODEL}")


def _normalize_bedrock_model_id(model_id: str, region: str) -> str:
    """
    Ensure the Bedrock model ID has the appropriate inference profile prefix.
    If the model_id already has a prefix (apac., au., us., eu., global.), leave it as-is.
    """
    prefixes = ("apac.", "au.", "us.", "eu.", "global.")
    if any(model_id.startswith(p) for p in prefixes):
        return model_id  # already prefixed — no change needed

    # Auto-prefix bare model IDs based on region
    if "claude" in model_id.lower():
        if region.startswith("ap-southeast-2"):
            return f"au.{model_id}"
        elif region.startswith("ap-"):
            return f"apac.{model_id}"
        elif region.startswith("us-"):
            return f"us.{model_id}"
        elif region.startswith("eu-"):
            return f"eu.{model_id}"
    elif "nova" in model_id.lower():
        if region.startswith("ap-"):
            return f"apac.{model_id}"
        elif region.startswith("us-"):
            return f"us.{model_id}"

    return model_id


def create_bedrock_chat(model_id: str | None = None) -> ChatBedrockConverse:
    """Create a ChatBedrockConverse instance with auto-normalized model ID."""
    target_model = model_id or BEDROCK_CHAT_MODEL
    normalized_id = _normalize_bedrock_model_id(target_model, AWS_REGION)

    client_kwargs: dict[str, Any] = {
        "model": normalized_id,
        "region_name": AWS_REGION,
        "temperature": 0.3,
    }
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY

    logger.debug(f"[Bedrock] Creating chat client: {normalized_id} (region={AWS_REGION})")
    return ChatBedrockConverse(**client_kwargs)


class ResilientBedrockLLM:
    """
    A resilient wrapper around ChatBedrockConverse.

    - Primary model: whatever BEDROCK_CHAT_MODEL is set to (default: apac.amazon.nova-lite-v1:0)
    - If the primary model hits a permission / resource error (e.g. Anthropic Claude
      pending use-case form approval), it automatically falls back to Nova Lite.
    - When BEDROCK_CHAT_MODEL is already a Nova model, the fallback is a no-op in practice.
    """

    _PERMISSION_ERRORS = ("ResourceNotFoundException", "ValidationException", "AccessDeniedException")

    def __init__(self, primary_model_id: str | None = None):
        self.primary_model_id = primary_model_id or BEDROCK_CHAT_MODEL
        self._llm = create_bedrock_chat(self.primary_model_id)
        self._fallback_llm: ChatBedrockConverse | None = None

    def _needs_fallback(self, error: Exception) -> bool:
        err_str = str(error)
        return any(code in err_str for code in self._PERMISSION_ERRORS)

    def _get_fallback_llm(self) -> ChatBedrockConverse:
        if self._fallback_llm is None:
            fallback_id = (
                "apac.amazon.nova-lite-v1:0"
                if AWS_REGION.startswith("ap-")
                else "us.amazon.nova-lite-v1:0"
            )
            logger.warning(f"[Bedrock] Falling back to {fallback_id} (primary model needs permissions).")
            self._fallback_llm = create_bedrock_chat(fallback_id)
        return self._fallback_llm

    def invoke(self, *args, **kwargs):
        try:
            return self._llm.invoke(*args, **kwargs)
        except Exception as e:
            if self._needs_fallback(e):
                logger.warning(f"[Bedrock] Primary model invoke failed — using Nova fallback. ({e})")
                return self._get_fallback_llm().invoke(*args, **kwargs)
            raise

    def with_structured_output(self, schema, **kwargs):
        primary_structured = self._llm.with_structured_output(schema, **kwargs)

        class ResilientStructuredRunnable:
            def __init__(inner_self, outer: "ResilientBedrockLLM", schema):
                inner_self.outer = outer
                inner_self.schema = schema
                inner_self.runnable = primary_structured

            def invoke(inner_self, *args, **kwargs):
                try:
                    return inner_self.runnable.invoke(*args, **kwargs)
                except Exception as e:
                    if inner_self.outer._needs_fallback(e):
                        logger.warning(
                            f"[Bedrock] Primary structured call failed — using Nova fallback. ({e})"
                        )
                        fallback_structured = inner_self.outer._get_fallback_llm().with_structured_output(
                            inner_self.schema
                        )
                        return fallback_structured.invoke(*args, **kwargs)
                    raise

        return ResilientStructuredRunnable(self, schema)


# Default shared LLM instance used by all LangGraph nodes
llm = ResilientBedrockLLM()
