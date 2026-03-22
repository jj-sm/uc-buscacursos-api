"""
Periodic updater that checks the jj-sm/buscacursos-dl-jj-sm GitHub repository
for new releases.  A "new release" means a release whose tag is not yet
present as a semester table in the local courses database.

The check interval (default: monthly = 30 days) can be changed at runtime
via the admin endpoint POST /admin/courses/update-frequency.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import requests

from .course_db import COURSES_DB_PATH, _SEMESTER_RE

# ── Configuration ──────────────────────────────────────────────────────────────

REPO_OWNER = "jj-sm"
REPO_NAME = "buscacursos-dl-jj-sm"

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Default interval: env-configurable, fallback 30 days in seconds
DEFAULT_INTERVAL_SECONDS: int = int(
    os.getenv("COURSES_UPDATE_INTERVAL_SECONDS", str(30 * 24 * 60 * 60))
)

# Runtime-mutable interval and metadata (updated via admin endpoint)
_state: dict = {
    "interval_seconds": DEFAULT_INTERVAL_SECONDS,
    "last_check": None,       # ISO string or None
    "last_result": None,      # human-readable string
    "checking": False,
}

# ── Logging ────────────────────────────────────────────────────────────────────

logger = logging.getLogger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _gh_headers() -> dict:
    h = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h


def get_latest_releases(per_page: int = 10) -> list[dict]:
    """Return the most recent releases from the upstream repo."""
    url = (
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        f"/releases?per_page={per_page}"
    )
    try:
        resp = requests.get(url, headers=_gh_headers(), timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        logger.error("Failed to fetch releases: %s", exc)
        return []


def _existing_semester_tables() -> set[str]:
    """Return the set of semester table names already in the local DB."""
    if not COURSES_DB_PATH.exists():
        return set()
    conn = sqlite3.connect(str(COURSES_DB_PATH))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'semester_%'"
        ).fetchall()
        return {r[0] for r in rows}
    finally:
        conn.close()


def _tag_to_table_name(tag: str) -> str | None:
    """
    Convert a release tag like "2025_2" or "semester_2025_2" into the
    canonical table name "semester_2025_2".  Returns None if the tag
    cannot be mapped to a valid semester name.
    """
    # Already fully qualified
    if _SEMESTER_RE.match(tag):
        return tag
    # Bare "YYYY_N" pattern
    if re.match(r"^\d{4}_\d+$", tag):
        return f"semester_{tag}"
    # v-prefixed: "v2025_2" or "v2025.2"
    stripped = re.sub(r"^v", "", tag).replace(".", "_")
    candidate = f"semester_{stripped}"
    if _SEMESTER_RE.match(candidate):
        return candidate
    return None


def _download_and_merge(asset_url: str, tag: str) -> bool:
    """
    Download the SQLite asset at *asset_url* and merge all semester tables
    that don't yet exist in the local database.
    """
    tmp_path = COURSES_DB_PATH.with_suffix(".tmp_dl")
    COURSES_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    headers = {"Accept": "application/octet-stream"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        logger.info("Downloading DB from %s …", asset_url)
        with requests.get(asset_url, headers=headers, stream=True, timeout=300) as r:
            r.raise_for_status()
            with open(tmp_path, "wb") as fh:
                for chunk in r.iter_content(chunk_size=65536):
                    fh.write(chunk)

        # If no local DB exists yet, just move the downloaded file
        if not COURSES_DB_PATH.exists():
            shutil.move(str(tmp_path), str(COURSES_DB_PATH))
            logger.info("Courses DB created at %s", COURSES_DB_PATH)
            return True

        # Merge: attach downloaded DB and copy any missing semester tables
        existing = _existing_semester_tables()
        src = sqlite3.connect(str(tmp_path))
        dst = sqlite3.connect(str(COURSES_DB_PATH))
        try:
            src_tables = [
                r[0]
                for r in src.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'semester_%'"
                ).fetchall()
            ]
            new_tables = [t for t in src_tables if t not in existing]
            if not new_tables:
                logger.info("No new semester tables found in downloaded DB for tag %s", tag)
                return False

            for table in new_tables:
                # Retrieve CREATE statement
                ddl = src.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (table,),
                ).fetchone()[0]
                dst.execute(ddl)
                rows = src.execute(f"SELECT * FROM [{table}]").fetchall()  # noqa: S608 – table validated via sqlite_master query above
                cols = len(rows[0]) if rows else 0
                if rows:
                    placeholders = ",".join(["?"] * cols)
                    dst.executemany(
                        f"INSERT OR IGNORE INTO [{table}] VALUES ({placeholders})",  # noqa: S608
                        [tuple(r) for r in rows],
                    )
                dst.commit()
                logger.info("Merged table %s (%d rows)", table, len(rows))

            return bool(new_tables)
        finally:
            src.close()
            dst.close()

    except Exception as exc:
        logger.error("Failed to download/merge DB: %s", exc)
        return False
    finally:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)


# ── Main check logic ───────────────────────────────────────────────────────────

async def check_and_update() -> dict:
    """
    Check upstream for new semester releases and merge any that are missing.
    Returns a status dict suitable for the admin API response.
    """
    _state["checking"] = True
    _state["last_check"] = datetime.now(timezone.utc).isoformat()
    updated_tables: list[str] = []

    try:
        releases = get_latest_releases()
        if not releases:
            _state["last_result"] = "No releases found or network error."
            return {"updated": False, "message": _state["last_result"]}

        existing = _existing_semester_tables()

        for release in releases:
            tag = release.get("tag_name", "")
            table_name = _tag_to_table_name(tag)
            if not table_name:
                continue
            if table_name in existing:
                continue

            # Found a new semester – locate the SQLite asset
            asset_url = None
            for asset in release.get("assets", []):
                name: str = asset.get("name", "")
                if name.endswith(".db") or name.endswith(".sqlite") or name.endswith(".s3db"):
                    asset_url = asset.get("url")
                    break

            if not asset_url:
                logger.warning("No DB asset found in release %s", tag)
                continue

            if _download_and_merge(asset_url, tag):
                updated_tables.append(table_name)
                existing.add(table_name)

        if updated_tables:
            msg = f"Merged new semester(s): {', '.join(updated_tables)}"
        else:
            msg = "Database is already up to date."

        _state["last_result"] = msg
        return {"updated": bool(updated_tables), "new_semesters": updated_tables, "message": msg}

    finally:
        _state["checking"] = False


# ── Background task ────────────────────────────────────────────────────────────

async def periodic_course_updater():
    """Runs the semester check periodically in the background."""
    logger.info(
        "Starting periodic courses updater (interval=%ds)…",
        _state["interval_seconds"],
    )
    while True:
        try:
            result = await check_and_update()
            logger.info("Courses update check result: %s", result)
        except Exception as exc:
            logger.error("Unhandled error in periodic_course_updater: %s", exc)
        await asyncio.sleep(_state["interval_seconds"])


# ── Public state accessors (used by admin router) ──────────────────────────────

def get_update_state() -> dict:
    return {
        "interval_seconds": _state["interval_seconds"],
        "interval_description": _describe_interval(_state["interval_seconds"]),
        "last_check": _state["last_check"],
        "last_result": _state["last_result"],
        "is_checking": _state["checking"],
    }


def set_update_interval(seconds: int) -> None:
    _state["interval_seconds"] = seconds


def _describe_interval(seconds: int) -> str:
    if seconds < 3600:
        return f"{seconds // 60} minute(s)"
    if seconds < 86400:
        return f"{seconds // 3600} hour(s)"
    return f"{seconds // 86400} day(s)"
