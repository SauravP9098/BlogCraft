from __future__ import annotations

import logging
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from backend.config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    S3_BUCKET_NAME,
    S3_PUBLIC_BASE_URL,
    S3_REGION,
)

logger = logging.getLogger(__name__)


def get_s3_client():
    client_kwargs = {"region_name": S3_REGION}
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        client_kwargs["aws_access_key_id"] = AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = AWS_SECRET_ACCESS_KEY
    return boto3.client("s3", **client_kwargs)


def upload_bytes_to_s3(
    data: bytes, s3_key: str, content_type: str = "image/png"
) -> str | None:
    """
    Upload raw bytes to Amazon S3. Returns the public/direct URL or None on failure.
    """
    if not S3_BUCKET_NAME:
        return None

    try:
        s3 = get_s3_client()
        extra_args = {"ContentType": content_type}
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=data,
            **extra_args,
        )
        url = f"{S3_PUBLIC_BASE_URL}/{s3_key}" if S3_PUBLIC_BASE_URL else f"https://{S3_BUCKET_NAME}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        logger.info(f"[S3] Uploaded {len(data)} bytes to {url}")
        return url
    except ClientError as e:
        logger.warning(f"[S3] Upload failed for {s3_key}: {e}")
        return None
    except Exception as e:
        logger.warning(f"[S3] Unexpected upload error for {s3_key}: {e}")
        return None


def upload_file_to_s3(
    local_path: Path, s3_key: str, content_type: str | None = None
) -> str | None:
    """
    Upload a local file to Amazon S3.
    """
    if not S3_BUCKET_NAME or not local_path.exists():
        return None

    try:
        data = local_path.read_bytes()
        ct = content_type or ("text/markdown" if local_path.suffix == ".md" else "application/octet-stream")
        return upload_bytes_to_s3(data, s3_key, content_type=ct)
    except Exception as e:
        logger.warning(f"[S3] Failed to read/upload file {local_path}: {e}")
        return None
