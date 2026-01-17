from __future__ import annotations

import hashlib
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class ArtifactSummary:
    artifact_id: str
    conversation_id: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    note: str
    created_at: str


class ArtifactStore:
    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path
        self._ensure_parent_dir()
        self._init_schema()

    def _ensure_parent_dir(self) -> None:
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    note TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    data_blob BLOB NOT NULL
                );
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_conv_time ON artifacts(conversation_id, created_at);")
            conn.commit()

    def add_artifact(
        self,
        conversation_id: str,
        filename: str,
        mime_type: str,
        data: bytes,
        note: str = "",
        max_bytes: int = 15 * 1024 * 1024,
    ) -> ArtifactSummary:
        if not conversation_id:
            raise ValueError("conversation_id が空です")
        if not filename:
            raise ValueError("filename が空です")
        if not mime_type:
            mime_type = "application/octet-stream"
        if data is None:
            raise ValueError("data が空です")

        size = len(data)
        if size > max_bytes:
            raise ValueError(f"ファイルが大きすぎます（上限 {max_bytes} bytes）")

        artifact_id = str(uuid.uuid4())
        created_at = _now_iso_utc()
        digest = _sha256(data)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO artifacts
                (artifact_id, conversation_id, filename, mime_type, size_bytes, sha256, note, created_at, data_blob)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (artifact_id, conversation_id, filename, mime_type, size, digest, note or "", created_at, data),
            )
            conn.commit()

        return ArtifactSummary(
            artifact_id=artifact_id,
            conversation_id=conversation_id,
            filename=filename,
            mime_type=mime_type,
            size_bytes=size,
            sha256=digest,
            note=note or "",
            created_at=created_at,
        )

    def list_artifacts(self, conversation_id: str, limit: int = 200) -> List[ArtifactSummary]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT artifact_id, conversation_id, filename, mime_type, size_bytes, sha256, note, created_at
                FROM artifacts
                WHERE conversation_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            ).fetchall()

        return [
            ArtifactSummary(
                artifact_id=r["artifact_id"],
                conversation_id=r["conversation_id"],
                filename=r["filename"],
                mime_type=r["mime_type"],
                size_bytes=int(r["size_bytes"]),
                sha256=r["sha256"],
                note=r["note"] or "",
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def get_artifact_bytes(self, artifact_id: str) -> bytes:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data_blob FROM artifacts WHERE artifact_id = ?",
                (artifact_id,),
            ).fetchone()
        if not row:
            raise KeyError("artifact not found")
        return bytes(row["data_blob"])
