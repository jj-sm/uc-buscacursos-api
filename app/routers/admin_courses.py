"""
Admin sub-router for courses DB update management.

Endpoints
---------
GET  /admin/courses/update-status   – current updater state
POST /admin/courses/update-check    – trigger an immediate check
POST /admin/courses/update-frequency – change the check interval
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
from ..deps import get_api_key
from ..course_updater import (
    check_and_update,
    get_update_state,
    set_update_interval,
    DEFAULT_INTERVAL_SECONDS,
)

router = APIRouter()

_UPDATE_STATUS_RESPONSES = {
    200: {
        "description": "Current updater status",
        "content": {
            "application/json": {
                "example": {
                    "interval_seconds": 2592000,
                    "interval_description": "30 day(s)",
                    "last_check": "2026-03-01T12:00:00",
                    "last_result": "Database is already up to date.",
                    "is_checking": False,
                }
            }
        },
    }
}

_UPDATE_CHECK_RESPONSES = {
    200: {
        "description": "Result of the update check",
        "content": {
            "application/json": {
                "example": {
                    "updated": True,
                    "new_semesters": ["semester_2026_2"],
                    "message": "Merged new semester(s): semester_2026_2",
                }
            }
        },
    }
}

_UPDATE_FREQUENCY_RESPONSES = {
    200: {
        "description": "Update frequency changed",
        "content": {
            "application/json": {
                "example": {
                    "interval_seconds": 86400,
                    "interval_description": "1 day(s)",
                    "message": "Update interval changed to 86400 seconds (1 day(s))",
                }
            }
        },
    },
    400: {
        "description": "Invalid interval value",
        "content": {"application/json": {"example": {"detail": "interval_seconds must be >= 60"}}},
    },
}


@router.get(
    "/update-status",
    summary="Courses update status",
    description=(
        "Returns the current state of the courses DB auto-updater, including "
        "the configured interval, the timestamp of the last check, and the "
        "result of that check."
    ),
    responses=_UPDATE_STATUS_RESPONSES,
    tags=["Admin – Courses"],
)
def get_courses_update_status(_auth: tuple = Depends(get_api_key)):
    return get_update_state()


@router.post(
    "/update-check",
    summary="Trigger immediate courses update check",
    description=(
        "Forces an immediate check against the upstream `jj-sm/buscacursos-dl-jj-sm` "
        "GitHub repository for new semester releases and merges any that are missing "
        "from the local database.  Admin API key required."
    ),
    responses=_UPDATE_CHECK_RESPONSES,
    tags=["Admin – Courses"],
)
async def trigger_courses_update(_auth: tuple = Depends(get_api_key)):
    result = await check_and_update()
    return result


@router.post(
    "/update-frequency",
    summary="Change courses update check frequency",
    description=(
        "Sets how often (in seconds) the background task checks for new semesters. "
        "The minimum allowed value is 60 seconds. "
        "The new interval takes effect on the **next** sleep cycle. "
        "Admin API key required."
    ),
    responses=_UPDATE_FREQUENCY_RESPONSES,
    tags=["Admin – Courses"],
)
def set_courses_update_frequency(
    interval_seconds: int = Query(
        DEFAULT_INTERVAL_SECONDS,
        ge=60,
        description="New interval in seconds (minimum 60)",
    ),
    _auth: tuple = Depends(get_api_key),
):
    if interval_seconds < 60:
        raise HTTPException(status_code=400, detail="interval_seconds must be >= 60")
    set_update_interval(interval_seconds)
    state = get_update_state()
    return {
        "interval_seconds": state["interval_seconds"],
        "interval_description": state["interval_description"],
        "message": (
            f"Update interval changed to {interval_seconds} seconds "
            f"({state['interval_description']})"
        ),
    }
