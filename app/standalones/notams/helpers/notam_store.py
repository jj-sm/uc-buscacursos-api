import os
import sqlite3
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

# Resolve to repo_root/data/notams.db so it works locally and in Docker (/app/data)
NOTAMS_DB_PATH = os.getenv(
    "NOTAMS_DB_PATH",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "notams.db")),
)

CREATE_SQL = """
PRAGMA foreign_keys = OFF;

-- Parsed/migrated NOTAMs for consumers that read from DB
CREATE TABLE IF NOT EXISTS notams (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  location TEXT,
  notam_lta_number TEXT,
  class TEXT,
  issue_date_utc TEXT,
  effective_date_utc TEXT,
  expiration_date_utc TEXT,
  notam_condition_subject_title TEXT,
  raw_text TEXT,
  uploaded_at TEXT,
  ivao_active BOOLEAN NOT NULL DEFAULT 0 CHECK (ivao_active IN (0,1)),
  data_source TEXT DEFAULT 'unknown' 
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_notams_location_number
  ON notams(location, notam_lta_number);

-- Raw uploaded files (store bytes in BLOB)
CREATE TABLE IF NOT EXISTS notam_files (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT,
  uploaded_at TEXT,
  content BLOB
);

CREATE INDEX IF NOT EXISTS idx_notam_files_uploaded_at
  ON notam_files(uploaded_at);
"""

def _get_conn():
    os.makedirs(os.path.dirname(NOTAMS_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(NOTAMS_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.executescript(CREATE_SQL)
        conn.commit()
    finally:
        conn.close()

def save_file(filename: str, content: Union[bytes, bytearray], uploaded_at: Optional[str] = None) -> int:
    """
    Save the uploaded file content (bytes) and return its DB id (notam_files.id).
    """
    if not isinstance(content, (bytes, bytearray)):
        raise TypeError("save_file expects bytes content")
    init_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        if uploaded_at is None:
            uploaded_at = datetime.utcnow().isoformat() + "Z"
        cur.execute(
            "INSERT INTO notam_files (filename, uploaded_at, content) VALUES (?, ?, ?)",
            (filename, uploaded_at, sqlite3.Binary(content)),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def insert_notam(location: str, notam_lta_number: str, klass: str,
                 issue_date_utc: str, effective_date_utc: str,
                 expiration_date_utc: str, notam_condition_subject_title: str,
                 raw_text: str, uploaded_at: Optional[str] = None,
                 data_source: str='FAA', ivao_active: int=0) -> int:
    """
    Upsert NOTAM by (location, notam_lta_number).
    """
    init_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        if uploaded_at is None:
            uploaded_at = datetime.utcnow().isoformat() + "Z"
        cur.execute("""
            INSERT OR REPLACE INTO notams (
                id, location, notam_lta_number, class, issue_date_utc,
                effective_date_utc, expiration_date_utc,
                notam_condition_subject_title, raw_text, uploaded_at, ivao_active, data_source
            )
            VALUES (
                (SELECT id FROM notams WHERE location = ? AND notam_lta_number = ?),
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            location, notam_lta_number,
            location, notam_lta_number, klass, issue_date_utc,
            effective_date_utc, expiration_date_utc,
            notam_condition_subject_title, raw_text, uploaded_at,
            ivao_active, data_source
        ))
        conn.commit()
        return cur.lastrowid or cur.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        conn.close()

def get_all_files() -> List[Dict[str, Any]]:
    """
    Returns [{'id', 'filename', 'uploaded_at', 'content'}, ...] with content as bytes.
    """
    init_db()
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, filename, uploaded_at, content FROM notam_files ORDER BY uploaded_at ASC")
        rows = cur.fetchall()
        out = []
        for r in rows:
            d = dict(r)
            # content is bytes already
            out.append(d)
        return out
    finally:
        conn.close()