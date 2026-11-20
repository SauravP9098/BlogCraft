from __future__ import annotations

import base64
import json
import logging
import os
import boto3
from backend.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    BEDROCK_IMAGE_MODEL,
)
from backend.tools.gemini_image import _gemini_generate_image_bytes

logger = logging.getLogger(__name__)


def _bedrock_generate_image_bytes(prompt: str) -> bytes:
    """
    Generate image bytes using Amazon Bedrock image models (Nova Canvas, Titan Image Generator, or Stability).
    Falls back gracefully if Bedrock image model access is not enabled.
    """
    model_id = (BEDROCK_IMAGE_MODEL or "").strip()

    # Guard: if model_id is a text model (e.g. nova-lite, nova-micro, claude), don't send image requests
    is_text_model = any(k in model_id.lower() for k in ["lite", "micro", "claude", "chat", "text"])
    if not model_id or is_text_model:
        # Default to Nova Canvas if available
        model_id = "amazon.nova-canvas-v1:0"

    image_region = os.getenv("BEDROCK_IMAGE_REGION", "us-east-1")
    client_kwargs = {"region_name": image_region}
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY

    try:
        client = boto3.client("bedrock-runtime", **client_kwargs)

        if "titan" in model_id.lower():
            body = json.dumps({
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {"text": prompt},
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 1024,
                    "width": 1024,
                    "cfgScale": 8.0,
                },
            })
            resp = client.invoke_model(
                modelId=model_id,
                body=body,
                accept="application/json",
                contentType="application/json",
            )
            data = json.loads(resp["body"].read())
            return base64.b64decode(data["images"][0])

        elif "canvas" in model_id.lower():
            body = json.dumps({
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {"text": prompt},
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 1024,
                    "width": 1024,
                    "quality": "standard",
                },
            })
            resp = client.invoke_model(
                modelId=model_id,
                body=body,
                accept="application/json",
                contentType="application/json",
            )
            data = json.loads(resp["body"].read())
            return base64.b64decode(data["images"][0])

        elif "stability" in model_id.lower() or "sd3" in model_id.lower():
            body = json.dumps({"prompt": prompt, "output_format": "png"})
            resp = client.invoke_model(
                modelId=model_id,
                body=body,
                accept="application/json",
                contentType="application/json",
            )
            data = json.loads(resp["body"].read())
            img_b64 = data.get("images", [None])[0] or data.get("image")
            if img_b64:
                return base64.b64decode(img_b64)

    except Exception as e:
        logger.info(f"[Bedrock Image] {model_id} access not active on AWS account ({type(e).__name__}). Using fallback.")

    # Fallback to Gemini if configured
    if os.getenv("GOOGLE_API_KEY"):
        try:
            return _gemini_generate_image_bytes(prompt)
        except Exception:
            pass

    raise RuntimeError("Image model access not enabled on AWS account.")
