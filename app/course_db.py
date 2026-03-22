"""
Course database connection using raw sqlite3.

The courses database contains dynamic tables named `semester_YYYY_N`
(e.g. semester_2025_2, semester_2026_1). Because table names are not
known at startup we bypass SQLAlchemy's ORM and query via the stdlib
sqlite3 module so we can parameterise the table name safely after
validating it against the live schema.
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Generator

COURSES_DATABASE_URL = os.getenv(
    "COURSES_DATABASE_URL",
    "sqlite:///./data/courses.sqlite",
)

# Parse the file path from a sqlite:///... URL
_raw_path = COURSES_DATABASE_URL.removeprefix("sqlite:///")
COURSES_DB_PATH = Path(_raw_path)
SEED_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "courses.sqlite"

# Semester name must be: semester_YYYY_N (digits only, safety whitelist)
_SEMESTER_RE = re.compile(r"^semester_\d{4}_\d+$")


def _bootstrap_db_if_needed() -> None:
    """
    Ensure a writable courses database exists at COURSES_DB_PATH.

    If the target file is missing but a bundled seed exists, copy the seed to
    the data directory so containers with a mounted volume start with data.
    """
    COURSES_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not COURSES_DB_PATH.exists() and SEED_DB_PATH.exists():
        COURSES_DB_PATH.write_bytes(SEED_DB_PATH.read_bytes())


def _connect() -> sqlite3.Connection:
    _bootstrap_db_if_needed()
    conn = sqlite3.connect(str(COURSES_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_course_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency that yields a raw sqlite3 connection."""
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def is_valid_semester(name: str) -> bool:
    """Return True if *name* is a safe, recognised semester table name."""
    if not _SEMESTER_RE.match(name):
        return False
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (name,),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def list_semesters(conn: sqlite3.Connection) -> list[str]:
    """Return all semester table names sorted chronologically."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'semester_%' ORDER BY name"
    ).fetchall()
    return [r["name"] for r in rows]
