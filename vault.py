"""
File vault helpers for storing and retrieving common job descriptions and resumes.
"""

import json
import uuid
from typing import List, Dict, Any
from pathlib import Path

from db import get_db, utcnow_str
from storage import save_bytes


def _exec(conn, query: str, params: tuple):
    if conn.__class__.__module__.startswith("psycopg2"):
        query = query.replace("?", "%s")
    cur = conn.cursor()
    cur.execute(query, params)
    return cur


def save_asset(user_id: str, kind: str, original_name: str, content: bytes, metadata: Dict[str, Any] = None) -> str:
    stored_path, file_hash = save_bytes(content, original_name)
    asset_id = str(uuid.uuid4())
    now = utcnow_str()

    with get_db() as conn:
        _exec(
            conn,
            """
            INSERT INTO file_assets (id, user_id, kind, original_name, stored_path, metadata_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                asset_id,
                user_id,
                kind,
                original_name,
                stored_path,
                json.dumps(metadata or {"file_hash": file_hash}),
                now,
            ),
        )
        conn.commit()

    return asset_id


def list_assets(user_id: str, kind: str) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cur = _exec(
            conn,
            "SELECT id, original_name, stored_path, metadata_json, created_at FROM file_assets WHERE user_id = ? AND kind = ? ORDER BY created_at DESC",
            (user_id, kind),
        )
        rows = cur.fetchall()
        assets = []
        for row in rows:
            assets.append(
                {
                    "id": row[0],
                    "original_name": row[1],
                    "stored_path": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "created_at": row[4],
                }
            )
        return assets


def get_asset(asset_id: str) -> Dict[str, Any]:
    with get_db() as conn:
        cur = _exec(
            conn,
            "SELECT id, original_name, stored_path, metadata_json, created_at, user_id, kind FROM file_assets WHERE id = ?",
            (asset_id,),
        )
        row = cur.fetchone()
        if not row:
            return {}
        return {
            "id": row[0],
            "original_name": row[1],
            "stored_path": row[2],
            "metadata": json.loads(row[3]) if row[3] else {},
            "created_at": row[4],
            "user_id": row[5],
            "kind": row[6],
        }


def load_asset_content(asset: Dict[str, Any]) -> bytes:
    if not asset:
        return b""
    path = asset.get("stored_path")
    if not path or not Path(path).exists():
        return b""
    return Path(path).read_bytes()


