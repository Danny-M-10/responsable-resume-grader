"""
Simple file storage helper.

- Saves bytes to a local storage directory with a hashed filename to avoid collisions.
- Returns both the stored path and the hash used.
- Designed to be swapped for S3 later if needed.
"""

import hashlib
import os
from pathlib import Path
from typing import Tuple

DEFAULT_STORAGE_DIR = os.environ.get("STORAGE_DIR", "storage")


def ensure_storage_dir() -> Path:
    path = Path(DEFAULT_STORAGE_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_bytes(content: bytes, original_name: str) -> Tuple[str, str]:
    """
    Save bytes to storage directory with a hashed filename.

    Returns:
        stored_path (str), file_hash (str)
    """
    storage_dir = ensure_storage_dir()
    file_hash = hashlib.sha256(content).hexdigest()
    suffix = Path(original_name).suffix or ""
    stored_name = f"{file_hash}{suffix}"
    stored_path = storage_dir / stored_name

    with open(stored_path, "wb") as f:
        f.write(content)

    return str(stored_path), file_hash


