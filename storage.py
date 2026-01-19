"""
File storage helper with S3 support.

- Saves bytes to S3 with a hashed filename to avoid collisions.
- Falls back to local storage if S3 is not configured.
- Returns both the stored path/key and the hash used.
"""

import hashlib
import os
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# S3 Configuration (check multiple env var names for compatibility)
S3_BUCKET = os.environ.get("S3_BUCKET") or os.environ.get("STORAGE_BUCKET") or "crossroads-recruiting-storage"
S3_REGION = os.environ.get("AWS_REGION") or os.environ.get("STORAGE_REGION") or "us-east-2"
USE_S3 = os.environ.get("USE_S3", "true").lower() == "true"

# Local storage fallback
DEFAULT_STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage")

# Lazy-loaded S3 client
_s3_client = None


def get_s3_client():
    """Get or create S3 client (lazy initialization)"""
    global _s3_client
    if _s3_client is None:
        import boto3
        _s3_client = boto3.client('s3', region_name=S3_REGION)
    return _s3_client


def ensure_storage_dir() -> Path:
    """Ensure local storage directory exists"""
    path = Path(DEFAULT_STORAGE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_bytes(content: bytes, original_name: str) -> Tuple[str, str]:
    """
    Save bytes to storage (S3 or local filesystem).

    Returns:
        stored_path (str): S3 key (s3://bucket/key) or local path
        file_hash (str): SHA256 hash of content
    """
    file_hash = hashlib.sha256(content).hexdigest()
    suffix = Path(original_name).suffix or ""
    stored_name = f"{file_hash}{suffix}"

    if USE_S3:
        try:
            s3_client = get_s3_client()
            s3_key = f"uploads/{stored_name}"

            # Determine content type
            content_type = "application/octet-stream"
            if suffix.lower() == ".pdf":
                content_type = "application/pdf"
            elif suffix.lower() == ".docx":
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif suffix.lower() == ".txt":
                content_type = "text/plain"

            s3_client.put_object(
                Bucket=S3_BUCKET,
                Key=s3_key,
                Body=content,
                ContentType=content_type
            )

            stored_path = f"s3://{S3_BUCKET}/{s3_key}"
            logger.info(f"Saved file to S3: {stored_path}")
            return stored_path, file_hash

        except Exception as e:
            logger.error(f"Failed to save to S3, falling back to local storage: {e}")
            # Fall through to local storage

    # Local storage fallback
    storage_dir = ensure_storage_dir()
    stored_path = storage_dir / stored_name

    with open(stored_path, "wb") as f:
        f.write(content)

    logger.info(f"Saved file to local storage: {stored_path}")
    return str(stored_path), file_hash


def load_bytes(stored_path: str) -> Optional[bytes]:
    """
    Load bytes from storage (S3 or local filesystem).

    Args:
        stored_path: S3 URI (s3://bucket/key) or local path

    Returns:
        File content as bytes, or None if not found
    """
    if not stored_path:
        return None

    if stored_path.startswith("s3://"):
        try:
            # Parse S3 URI
            # Format: s3://bucket/key
            path_without_prefix = stored_path[5:]  # Remove "s3://"
            bucket, key = path_without_prefix.split("/", 1)

            s3_client = get_s3_client()
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            logger.debug(f"Loaded file from S3: {stored_path}")
            return content

        except Exception as e:
            logger.error(f"Failed to load from S3 {stored_path}: {e}")
            return None
    else:
        # Local file
        path = Path(stored_path)
        if not path.exists():
            logger.warning(f"Local file not found: {stored_path}")
            return None
        return path.read_bytes()


def delete_file(stored_path: str) -> bool:
    """
    Delete file from storage (S3 or local filesystem).

    Args:
        stored_path: S3 URI (s3://bucket/key) or local path

    Returns:
        True if deleted successfully, False otherwise
    """
    if not stored_path:
        return False

    if stored_path.startswith("s3://"):
        try:
            # Parse S3 URI
            path_without_prefix = stored_path[5:]
            bucket, key = path_without_prefix.split("/", 1)

            s3_client = get_s3_client()
            s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted file from S3: {stored_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete from S3 {stored_path}: {e}")
            return False
    else:
        # Local file
        try:
            path = Path(stored_path)
            if path.exists():
                path.unlink()
                logger.info(f"Deleted local file: {stored_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete local file {stored_path}: {e}")
            return False
