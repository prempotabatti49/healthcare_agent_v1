"""
S3 Service — store and retrieve original document files.

Why store originals in S3 if SuperMemory holds the embeddings?
  • SuperMemory stores processed text embeddings, not raw binaries.
  • Originals are needed for: re-processing, compliance/audit, user download.
  • S3 is the source of truth; SuperMemory is the search index.
"""
from __future__ import annotations

import logging
import mimetypes
import uuid
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()


def _client():
    return boto3.client(
        "s3",
        aws_access_key_id=_settings.aws_access_key_id or None,
        aws_secret_access_key=_settings.aws_secret_access_key or None,
        region_name=_settings.aws_region,
    )


def upload_document(
    file_bytes: bytes,
    filename: str,
    user_id: str,
    document_type: str = "other",
) -> Optional[str]:
    """
    Upload a document to S3 under:
      documents/{user_id}/{uuid}_{filename}

    Returns the S3 object key on success, None on failure.
    S3 bucket is configured via S3_BUCKET_NAME env var.
    """
    if not _settings.s3_bucket_name:
        logger.warning("S3_BUCKET_NAME not configured — skipping S3 upload")
        return None

    key = f"documents/{user_id}/{uuid.uuid4()}_{filename}"
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    try:
        _client().put_object(
            Bucket=_settings.s3_bucket_name,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
            Metadata={"user_id": user_id, "document_type": document_type},
        )
        logger.info("Uploaded %s to S3: %s", filename, key)
        return key
    except ClientError as exc:
        logger.error("S3 upload failed: %s", exc)
        return None


def get_presigned_url(s3_key: str, expiry_seconds: int = 3600) -> Optional[str]:
    """Generate a temporary pre-signed download URL for a document."""
    if not _settings.s3_bucket_name or not s3_key:
        return None
    try:
        url = _client().generate_presigned_url(
            "get_object",
            Params={"Bucket": _settings.s3_bucket_name, "Key": s3_key},
            ExpiresIn=expiry_seconds,
        )
        return url
    except ClientError as exc:
        logger.error("Presigned URL generation failed: %s", exc)
        return None
