import os
import secrets
import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth_db import get_auth_db
from ..auth_models import APIKey
from ..course_db import COURSES_DB_PATH, get_course_db
from ..api_helpers.common import add_welcome_endpoint
from ..deps import get_api_key
from dotenv import load_dotenv
from ..docs.responses import admin as r_admin

load_dotenv()
HIDE_ADMIN_ENDPOINTS = os.getenv("DEBUG", "0") == "1"

router = APIRouter()

add_welcome_endpoint(
    router,
    summary="Admin endpoints",
    description="This route lists the available admin endpoints.",
    tags=["Admin"],
)


def _ensure_admin(api_key_tuple: tuple) -> None:
    """Raise 403 unless the requester has enterprise/admin tier."""
    _, tier, _ = api_key_tuple
    if tier not in ("enterprise", "admin"):
        raise HTTPException(status_code=403, detail="Admin privileges required")


@router.post(
    "/keys",
    responses=r_admin.POST_ADMIN_KEYS,
    summary="Create API key (for admin use only)",
    include_in_schema=HIDE_ADMIN_ENDPOINTS,
)
def create_api_key(
    name: str,
    db: Session = Depends(get_auth_db),
    api_key_tuple: tuple = Depends(get_api_key),
):
    _ensure_admin(api_key_tuple)
    new_key = secrets.token_urlsafe(32)
    key_obj = APIKey(key=new_key, name=name)
    db.add(key_obj)
    db.commit()
    db.refresh(key_obj)
    return {"key": key_obj.key, "name": key_obj.name}


@router.get(
    "/keys/list",
    responses=r_admin.GET_ADMIN_KEYS_LIST,
    summary="List API keys (for admin use only)",
    include_in_schema=HIDE_ADMIN_ENDPOINTS,
)
def list_api_keys(
    db: Session = Depends(get_auth_db), api_key_tuple: tuple = Depends(get_api_key)
):
    _ensure_admin(api_key_tuple)
    keys = db.query(APIKey).all()
    return [{"id": k.id, "key": k.key, "name": k.name, "active": k.active} for k in keys]


@router.patch(
    "/keys/{key_name}",
    responses=r_admin.PATCH_ADMIN_KEYS_KEYNAME,
    summary="Deactivate API key (for admin use only)",
    include_in_schema=HIDE_ADMIN_ENDPOINTS
)
def deactivate_api_key(
    key_name: str,
    db: Session = Depends(get_auth_db),
    api_key_tuple: tuple = Depends(get_api_key),
):
    _ensure_admin(api_key_tuple)
    try:
        if key_name.isdigit():
            key_obj = db.query(APIKey).filter(APIKey.id == int(key_name)).first()
        else:
            key_obj = db.query(APIKey).filter(APIKey.name == key_name).first()

        if key_obj:
            key_obj.active = False
            db.commit()
            return {"status": "deactivated"}

        return HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))


@router.get(
    "/authenticated",
    responses=r_admin.GET_ADMIN_AUTHENTICATED,
    summary="Check for user authentication"
)
def authenticated(api_key_tuple: tuple = Depends(get_api_key)):
    if api_key_tuple:
        return {"status": "authenticated"}
    raise HTTPException(status_code=401, detail="Invalid API Key")


@router.post(
    "/courses/sql",
    summary="Execute read-only SQL against courses DB (admin only)",
    description=(
        "Runs a **read-only** SQL query against the courses database. "
        "Only SELECT/PRAGMA statements are allowed. "
        "Admin API key required."
    ),
    responses=r_admin.POST_ADMIN_SQL,
)
def run_admin_sql(
    sql: str,
    params: list[Any] | None = None,
    api_key_tuple: tuple = Depends(get_api_key),
    conn: sqlite3.Connection = Depends(get_course_db),
):
    _ensure_admin(api_key_tuple)

    if not sql.strip().lower().startswith(("select", "pragma")):
        raise HTTPException(status_code=400, detail="Only SELECT/PRAGMA statements are allowed")

    try:
        cur = conn.execute(sql, params or [])
        rows = [dict(r) for r in cur.fetchall()]
        return {"rows": rows, "count": len(rows)}
    except sqlite3.Error as exc:
        raise HTTPException(status_code=400, detail=f"SQL error: {exc}") from exc
