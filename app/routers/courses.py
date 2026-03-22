"""
Courses router – all endpoints for querying the UC BuscaCursos data.

Tier access rules
-----------------
* Free / Pro / Premium / Enterprise  → search, list, single-course lookup, metadata
* Pro+                               → streaming NDJSON  (GET /{semester}/stream)
* Premium+                           → semester statistics (GET /{semester}/stats)
"""

import json
import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import StreamingResponse

from ..api_helpers.common import add_welcome_endpoint
from ..course_db import get_course_db, is_valid_semester, list_semesters
from ..deps import get_api_key
from ..docs.responses import courses as r_courses

router = APIRouter()

add_welcome_endpoint(
    router,
    summary="Courses endpoints",
    description="Lists all available /courses endpoints.",
    tags=["Courses"],
)

# ── Helpers ────────────────────────────────────────────────────────────────────

_TIER_ORDER = ["free", "pro", "premium", "enterprise"]


def _require_tier(current_tier: str, minimum_tier: str, detail: str) -> None:
    """Raise 403 if *current_tier* is below *minimum_tier*."""
    if _TIER_ORDER.index(current_tier) < _TIER_ORDER.index(minimum_tier):
        raise HTTPException(status_code=403, detail=detail)


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def _validate_semester(semester: str, conn: sqlite3.Connection) -> None:
    """Raise 404 if *semester* is not a valid table in the DB."""
    if not is_valid_semester(semester):
        raise HTTPException(
            status_code=404,
            detail=f"Semester '{semester}' not found. Use GET /courses/semesters to list available semesters.",
        )


# ── 1. List semesters ──────────────────────────────────────────────────────────

@router.get(
    "/semesters",
    summary="List available semesters",
    description=(
        "Returns all semester table names currently available in the database, "
        "ordered chronologically."
    ),
    responses=r_courses.GET_SEMESTERS,
    tags=["Courses"],
)
def get_semesters(
    conn: sqlite3.Connection = Depends(get_course_db),
    _auth: tuple = Depends(get_api_key),
):
    semesters = list_semesters(conn)
    return {"semesters": semesters, "count": len(semesters)}


# ── 2. Search courses ──────────────────────────────────────────────────────────

@router.get(
    "/{semester}/search",
    summary="Search courses",
    description=(
        "Full-text and field-level search across courses in a given semester. "
        "Supports filtering by name, initials, teacher, school, area, credits, "
        "campus, format, category, is_english, and free-text query (`q`). "
        "Results are paginated."
    ),
    responses=r_courses.GET_SEARCH,
    tags=["Courses"],
)
def search_courses(
    semester: str = Path(..., description="Semester name, e.g. semester_2026_1"),
    q: Optional[str] = Query(None, description="Free-text search across name, initials, and teachers"),
    initials: Optional[str] = Query(None, description="Filter by course initials (exact, case-insensitive)"),
    name: Optional[str] = Query(None, description="Filter by course name (partial match, case-insensitive)"),
    teacher: Optional[str] = Query(None, description="Filter by teacher name (partial match)"),
    school: Optional[str] = Query(None, description="Filter by school"),
    area: Optional[str] = Query(None, description="Filter by area"),
    category: Optional[str] = Query(None, description="Filter by category"),
    campus: Optional[str] = Query(None, description="Filter by campus"),
    format: Optional[str] = Query(None, description="Filter by format (e.g. Presencial, Online)"),
    credits: Optional[int] = Query(None, description="Filter by exact number of credits"),
    is_english: Optional[bool] = Query(None, description="Filter English-language courses"),
    is_special: Optional[bool] = Query(None, description="Filter special courses"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=200, description="Results per page (max 200)"),
    conn: sqlite3.Connection = Depends(get_course_db),
    _auth: tuple = Depends(get_api_key),
):
    _validate_semester(semester, conn)

    conditions: list[str] = []
    params: list = []

    if q:
        conditions.append(
            "(LOWER(name) LIKE ? OR LOWER(initials) LIKE ? OR LOWER(teachers) LIKE ?)"
        )
        like = f"%{q.lower()}%"
        params.extend([like, like, like])
    if initials:
        conditions.append("LOWER(initials) = ?")
        params.append(initials.lower())
    if name:
        conditions.append("LOWER(name) LIKE ?")
        params.append(f"%{name.lower()}%")
    if teacher:
        conditions.append("LOWER(teachers) LIKE ?")
        params.append(f"%{teacher.lower()}%")
    if school:
        conditions.append("LOWER(school) = ?")
        params.append(school.lower())
    if area:
        conditions.append("LOWER(area) = ?")
        params.append(area.lower())
    if category:
        conditions.append("LOWER(category) = ?")
        params.append(category.lower())
    if campus:
        conditions.append("LOWER(campus) = ?")
        params.append(campus.lower())
    if format:
        conditions.append("LOWER(format) = ?")
        params.append(format.lower())
    if credits is not None:
        conditions.append("credits = ?")
        params.append(credits)
    if is_english is not None:
        conditions.append("is_english = ?")
        params.append(1 if is_english else 0)
    if is_special is not None:
        conditions.append("is_special = ?")
        params.append(1 if is_special else 0)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    count_sql = f"SELECT COUNT(*) FROM [{semester}] {where}"  # noqa: S608 – semester validated via is_valid_semester()
    total = conn.execute(count_sql, params).fetchone()[0]

    offset = (page - 1) * page_size
    data_sql = (
        f"SELECT * FROM [{semester}] {where} "  # noqa: S608 – semester validated via is_valid_semester()
        f"ORDER BY initials, section "
        f"LIMIT ? OFFSET ?"
    )
    rows = conn.execute(data_sql, params + [page_size, offset]).fetchall()

    return {
        "data": [_row_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


# ── 3. List all courses (paginated) ───────────────────────────────────────────

@router.get(
    "/{semester}/list",
    summary="List all courses (paginated)",
    description=(
        "Returns all courses for a semester with pagination. "
        "Use `page` and `page_size` to navigate large result sets."
    ),
    responses=r_courses.GET_LIST,
    tags=["Courses"],
)
def list_courses(
    semester: str = Path(..., description="Semester name, e.g. semester_2026_1"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    conn: sqlite3.Connection = Depends(get_course_db),
    _auth: tuple = Depends(get_api_key),
):
    _validate_semester(semester, conn)

    total = conn.execute(f"SELECT COUNT(*) FROM [{semester}]").fetchone()[0]  # noqa: S608
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"SELECT * FROM [{semester}] ORDER BY initials, section LIMIT ? OFFSET ?",  # noqa: S608
        [page_size, offset],
    ).fetchall()

    return {
        "data": [_row_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, (total + page_size - 1) // page_size),
    }


# ── 4. Get course by composite ID ─────────────────────────────────────────────

@router.get(
    "/{semester}/course/{course_id:path}",
    summary="Get course by ID",
    description="Retrieve a single course record by its composite primary key (e.g. IIC2233-1).",
    responses=r_courses.GET_COURSE_BY_ID,
    tags=["Courses"],
)
def get_course_by_id(
    semester: str = Path(..., description="Semester name"),
    course_id: str = Path(..., description="Course composite ID, e.g. IIC2233-1"),
    conn: sqlite3.Connection = Depends(get_course_db),
    _auth: tuple = Depends(get_api_key),
):
    _validate_semester(semester, conn)
    row = conn.execute(
        f"SELECT * FROM [{semester}] WHERE id = ?",  # noqa: S608
        (course_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
    return _row_to_dict(row)


# ── 5. Get course by NRC ───────────────────────────────────────────────────────

@router.get(
    "/{semester}/nrc/{nrc}",
    summary="Get course by NRC",
    description="Retrieve a single course section by its NRC (unique per semester).",
    responses=r_courses.GET_COURSE_BY_NRC,
    tags=["Courses"],
)
def get_course_by_nrc(
    semester: str = Path(..., description="Semester name"),
    nrc: str = Path(..., description="NRC code"),
    conn: sqlite3.Connection = Depends(get_course_db),
    _auth: tuple = Depends(get_api_key),
):
    _validate_semester(semester, conn)
    row = conn.execute(
        f"SELECT * FROM [{semester}] WHERE nrc = ?",  # noqa: S608
        (nrc,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"NRC '{nrc}' not found in {semester}")
    return _row_to_dict(row)


# ── 6. Get all sections of a course by initials ───────────────────────────────

@router.get(
    "/{semester}/initials/{initials}",
    summary="Get all sections by initials",
    description=(
        "Returns all sections (and their NRCs, teachers, schedules) "
        "for the given course initials."
    ),
    responses=r_courses.GET_COURSES_BY_INITIALS,
    tags=["Courses"],
)
def get_courses_by_initials(
    semester: str = Path(..., description="Semester name"),
    initials: str = Path(..., description="Course initials, e.g. IIC2233"),
    conn: sqlite3.Connection = Depends(get_course_db),
    _auth: tuple = Depends(get_api_key),
):
    _validate_semester(semester, conn)
    rows = conn.execute(
        f"SELECT * FROM [{semester}] WHERE LOWER(initials) = ? ORDER BY section",  # noqa: S608
        (initials.lower(),),
    ).fetchall()
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No sections found for initials '{initials}' in {semester}",
        )
    return {
        "initials": initials.upper(),
        "semester": semester,
        "sections": [_row_to_dict(r) for r in rows],
        "count": len(rows),
    }


# ── 7. Semester statistics (Premium+) ─────────────────────────────────────────

@router.get(
    "/{semester}/stats",
    summary="Semester statistics",
    description=(
        "Aggregated statistics for a semester. "
        "**Requires Premium tier or above.**"
    ),
    responses=r_courses.GET_STATS,
    tags=["Courses"],
)
def get_semester_stats(
    semester: str = Path(..., description="Semester name"),
    conn: sqlite3.Connection = Depends(get_course_db),
    auth: tuple = Depends(get_api_key),
):
    _, tier, _ = auth
    _require_tier(tier, "premium", "Stats endpoint requires Premium tier or above.")
    _validate_semester(semester, conn)

    total = conn.execute(f"SELECT COUNT(*) FROM [{semester}]").fetchone()[0]  # noqa: S608
    unique_initials = conn.execute(
        f"SELECT COUNT(DISTINCT initials) FROM [{semester}]"  # noqa: S608
    ).fetchone()[0]
    schools = conn.execute(
        f"SELECT COUNT(DISTINCT school) FROM [{semester}]"  # noqa: S608
    ).fetchone()[0]
    campuses_row = conn.execute(
        f"SELECT COUNT(DISTINCT campus) FROM [{semester}]"  # noqa: S608
    ).fetchone()[0]
    formats = [
        r[0]
        for r in conn.execute(
            f"SELECT DISTINCT format FROM [{semester}] WHERE format IS NOT NULL ORDER BY format"  # noqa: S608
        ).fetchall()
    ]
    english = conn.execute(
        f"SELECT COUNT(*) FROM [{semester}] WHERE is_english = 1"  # noqa: S608
    ).fetchone()[0]
    avg_credits_row = conn.execute(
        f"SELECT AVG(credits) FROM [{semester}] WHERE credits IS NOT NULL"  # noqa: S608
    ).fetchone()[0]
    avg_quota_row = conn.execute(
        f"SELECT AVG(total_quota) FROM [{semester}] WHERE total_quota IS NOT NULL"  # noqa: S608
    ).fetchone()[0]

    return {
        "semester": semester,
        "total_sections": total,
        "unique_initials": unique_initials,
        "schools": schools,
        "campuses": campuses_row,
        "formats": formats,
        "english_courses": english,
        "avg_credits": round(avg_credits_row, 2) if avg_credits_row else None,
        "avg_quota": round(avg_quota_row, 2) if avg_quota_row else None,
    }


# ── 8. Streaming NDJSON (Pro+) ─────────────────────────────────────────────────

@router.get(
    "/{semester}/stream",
    summary="Stream all courses (NDJSON)",
    description=(
        "Streams every course row in the semester as Newline-Delimited JSON (NDJSON). "
        "Each line is a complete JSON object. "
        "**Requires Pro tier or above.**"
    ),
    responses=r_courses.GET_STREAM,
    tags=["Courses"],
)
def stream_courses(
    semester: str = Path(..., description="Semester name"),
    conn: sqlite3.Connection = Depends(get_course_db),
    auth: tuple = Depends(get_api_key),
):
    _, tier, _ = auth
    _require_tier(tier, "pro", "Streaming requires Pro tier or above.")
    _validate_semester(semester, conn)

    def _generate():
        # Use a fresh connection for the generator to avoid threading issues
        from ..course_db import COURSES_DB_PATH as _path
        import sqlite3 as _sqlite3

        stream_conn = _sqlite3.connect(str(_path), check_same_thread=False)
        stream_conn.row_factory = _sqlite3.Row
        try:
            cursor = stream_conn.execute(
                f"SELECT * FROM [{semester}] ORDER BY initials, section"  # noqa: S608
            )
            for row in cursor:
                yield json.dumps(dict(row), default=str) + "\n"
        finally:
            stream_conn.close()

    return StreamingResponse(
        _generate(),
        media_type="application/x-ndjson",
        headers={"X-Semester": semester},
    )


# ── 9–12. Metadata lists ───────────────────────────────────────────────────────

def _make_metadata_endpoint(field: str, plural: str, tag_summary: str, tag_description: str):
    """Factory that registers a GET /{semester}/<plural> metadata endpoint."""

    @router.get(
        f"/{{semester}}/{plural}",
        summary=tag_summary,
        description=tag_description,
        responses=r_courses.GET_METADATA_LIST,
        tags=["Courses – Metadata"],
        name=f"list_{plural}",
    )
    def _endpoint(
        semester: str = Path(..., description="Semester name"),
        conn: sqlite3.Connection = Depends(get_course_db),
        _auth: tuple = Depends(get_api_key),
    ):
        _validate_semester(semester, conn)
        rows = conn.execute(
            f"SELECT DISTINCT [{field}] FROM [{semester}] "  # noqa: S608
            f"WHERE [{field}] IS NOT NULL ORDER BY [{field}]"
        ).fetchall()
        values = [r[0] for r in rows]
        return {"values": values, "count": len(values)}

    return _endpoint


_make_metadata_endpoint(
    "school", "schools",
    "List schools",
    "Returns all distinct school names present in the semester.",
)
_make_metadata_endpoint(
    "area", "areas",
    "List areas",
    "Returns all distinct academic areas present in the semester.",
)
_make_metadata_endpoint(
    "category", "categories",
    "List categories",
    "Returns all distinct course categories (e.g. RE, OFG, EL) in the semester.",
)
_make_metadata_endpoint(
    "campus", "campuses",
    "List campuses",
    "Returns all distinct campus names in the semester.",
)
_make_metadata_endpoint(
    "format", "formats",
    "List formats",
    "Returns all distinct delivery formats (e.g. Presencial, Online, Híbrido).",
)
_make_metadata_endpoint(
    "program", "programs",
    "List programs",
    "Returns all distinct academic programs in the semester.",
)


# ── 13. Teachers list ─────────────────────────────────────────────────────────

@router.get(
    "/{semester}/teachers",
    summary="List teachers",
    description=(
        "Returns all distinct teacher names present in the semester. "
        "The `teachers` field may contain comma-separated names; this endpoint "
        "returns them as stored (not exploded)."
    ),
    responses=r_courses.GET_METADATA_LIST,
    tags=["Courses – Metadata"],
)
def list_teachers(
    semester: str = Path(..., description="Semester name"),
    conn: sqlite3.Connection = Depends(get_course_db),
    _auth: tuple = Depends(get_api_key),
):
    _validate_semester(semester, conn)
    rows = conn.execute(
        f"SELECT DISTINCT teachers FROM [{semester}] WHERE teachers IS NOT NULL ORDER BY teachers"  # noqa: S608
    ).fetchall()
    values = [r[0] for r in rows]
    return {"values": values, "count": len(values)}
