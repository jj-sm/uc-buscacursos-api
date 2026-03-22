"""
Tests for the /courses endpoints.

These tests use an in-memory SQLite database pre-populated with two
semester tables so that all endpoint logic can be exercised without
hitting a real courses database or GitHub.
"""

import json
import os
import sqlite3
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Enable DEBUG mode so API key checks are bypassed
os.environ["DEBUG"] = "1"

# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_ROWS = [
    (
        "IIC2233-1", "IIC2233", 1, "10001", "Programacion Avanzada", 10,
        "IIC1103", None, None, None, "Ingenieria Civil", "Ingenieria",
        "Computacion", "RE", "Docente Uno", '{"MON": ["10:00"]}',
        "Presencial", "San Joaquin", 0, 1, 0, 40, None, "2026-03-01"
    ),
    (
        "IIC2233-2", "IIC2233", 2, "10002", "Programacion Avanzada", 10,
        "IIC1103", None, None, None, "Ingenieria Civil", "Ingenieria",
        "Computacion", "RE", "Docente Dos", '{"TUE": ["10:00"]}',
        "Online", "Casa Central", 0, 1, 0, 35, None, "2026-03-01"
    ),
    (
        "MAT1203-1", "MAT1203", 1, "20001", "Calculo III", 10,
        "MAT1202", None, None, None, "Ingenieria Civil", "Ciencias",
        "Matematicas", "OFG", "Prof Matematica",
        '{"WED": ["14:00"]}', "Presencial", "San Joaquin", 0, 0, 0, 50,
        None, "2026-03-01"
    ),
    (
        "ENG1001-1", "ENG1001", 1, "30001", "English for Engineers", 5,
        None, None, None, None, "Idiomas", "Letras", None, "EL",
        "Prof English", '{"FRI": ["09:00"]}', "Presencial", "Casa Central",
        1, 1, 0, 30, None, "2026-03-01"
    ),
]

CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS {table} (
        id TEXT PRIMARY KEY, initials TEXT NOT NULL, section INTEGER NOT NULL,
        nrc TEXT NOT NULL, name TEXT, credits INTEGER, req TEXT, conn TEXT,
        restr TEXT, equiv TEXT, program TEXT, school TEXT, area TEXT,
        category TEXT, teachers TEXT, schedule_json TEXT, format TEXT,
        campus TEXT, is_english INTEGER, is_removable INTEGER,
        is_special INTEGER, total_quota INTEGER, quota_json TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
"""

INSERT_SQL = """
    INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""


def _make_test_db(path: str, tables: list[str]) -> None:
    conn = sqlite3.connect(path)
    for table in tables:
        conn.execute(CREATE_TABLE_SQL.format(table=table))
        rows = [list(r) for r in SAMPLE_ROWS]
        # Make IDs unique per table
        for i, r in enumerate(rows):
            r[0] = f"{table}::{r[0]}"
        conn.executemany(INSERT_SQL.format(table=table), rows)
    conn.commit()
    conn.close()


@pytest.fixture(scope="module")
def courses_db(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("courses_data")
    db_path = str(db_dir / "courses.db")
    _make_test_db(db_path, ["semester_2025_2", "semester_2026_1"])
    return db_path


@pytest.fixture(scope="module")
def client(courses_db):
    os.environ["DEBUG"] = "1"
    os.environ["COURSES_DATABASE_URL"] = f"sqlite:///{courses_db}"

    # Re-import after env is set so course_db picks up the new URL
    import importlib
    import app.course_db as _cdb
    _cdb.COURSES_DATABASE_URL = os.environ["COURSES_DATABASE_URL"]
    _cdb.COURSES_DB_PATH = _cdb.Path(courses_db)

    from app.main import app
    with TestClient(app) as c:
        yield c


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestCoursesHealth:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


class TestSemesters:
    def test_list_semesters(self, client):
        r = client.get("/courses/semesters")
        assert r.status_code == 200
        data = r.json()
        assert "semesters" in data
        assert "count" in data
        assert data["count"] >= 2
        assert "semester_2025_2" in data["semesters"]
        assert "semester_2026_1" in data["semesters"]

    def test_semesters_sorted(self, client):
        r = client.get("/courses/semesters")
        sems = r.json()["semesters"]
        assert sems == sorted(sems)


class TestSearch:
    def test_search_by_initials(self, client):
        r = client.get("/courses/semester_2026_1/search?initials=IIC2233")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        for row in data["data"]:
            assert row["initials"] == "IIC2233"

    def test_search_by_q(self, client):
        r = client.get("/courses/semester_2026_1/search?q=avanzada")
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_search_by_is_english(self, client):
        r = client.get("/courses/semester_2026_1/search?is_english=true")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        for row in data["data"]:
            assert row["is_english"] == 1

    def test_search_pagination(self, client):
        r1 = client.get("/courses/semester_2026_1/search?page=1&page_size=2")
        assert r1.status_code == 200
        d1 = r1.json()
        assert len(d1["data"]) <= 2
        assert d1["page"] == 1

        r2 = client.get("/courses/semester_2026_1/search?page=2&page_size=2")
        d2 = r2.json()
        assert d2["page"] == 2

    def test_search_invalid_semester(self, client):
        r = client.get("/courses/semester_9999_9/search?q=test")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()


class TestList:
    def test_list_courses(self, client):
        r = client.get("/courses/semester_2026_1/list")
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] == 4

    def test_list_pagination(self, client):
        r = client.get("/courses/semester_2026_1/list?page=1&page_size=2")
        assert r.status_code == 200
        data = r.json()
        assert len(data["data"]) == 2
        assert data["pages"] == 2


class TestGetById:
    def test_get_course_by_id(self, client):
        r = client.get("/courses/semester_2026_1/list?page_size=1")
        row_id = r.json()["data"][0]["id"]
        r2 = client.get(f"/courses/semester_2026_1/course/{row_id}")
        assert r2.status_code == 200
        assert r2.json()["id"] == row_id

    def test_get_course_not_found(self, client):
        r = client.get("/courses/semester_2026_1/course/NONEXISTENT-99")
        assert r.status_code == 404

    def test_get_course_by_nrc(self, client):
        r = client.get("/courses/semester_2026_1/nrc/10001")
        assert r.status_code == 200
        assert r.json()["nrc"] == "10001"

    def test_get_course_by_nrc_not_found(self, client):
        r = client.get("/courses/semester_2026_1/nrc/99999")
        assert r.status_code == 404


class TestInitials:
    def test_get_by_initials(self, client):
        r = client.get("/courses/semester_2026_1/initials/IIC2233")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] == 2
        assert data["initials"] == "IIC2233"
        assert len(data["sections"]) == 2

    def test_initials_case_insensitive(self, client):
        r = client.get("/courses/semester_2026_1/initials/iic2233")
        assert r.status_code == 200
        assert r.json()["count"] == 2

    def test_initials_not_found(self, client):
        r = client.get("/courses/semester_2026_1/initials/ZZZ9999")
        assert r.status_code == 404


class TestMetadata:
    def test_list_schools(self, client):
        r = client.get("/courses/semester_2026_1/schools")
        assert r.status_code == 200
        data = r.json()
        assert "values" in data
        assert "count" in data
        assert data["count"] >= 2  # Ingenieria, Ciencias, Letras

    def test_list_areas(self, client):
        r = client.get("/courses/semester_2026_1/areas")
        assert r.status_code == 200
        assert r.json()["count"] >= 1

    def test_list_categories(self, client):
        r = client.get("/courses/semester_2026_1/categories")
        assert r.status_code == 200
        values = r.json()["values"]
        assert "RE" in values

    def test_list_campuses(self, client):
        r = client.get("/courses/semester_2026_1/campuses")
        assert r.status_code == 200
        values = r.json()["values"]
        assert len(values) >= 1

    def test_list_formats(self, client):
        r = client.get("/courses/semester_2026_1/formats")
        assert r.status_code == 200
        values = r.json()["values"]
        assert "Presencial" in values

    def test_list_teachers(self, client):
        r = client.get("/courses/semester_2026_1/teachers")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1


class TestStats:
    def test_stats_requires_premium(self, client):
        """In DEBUG mode the tier is 'enterprise', so stats should work."""
        r = client.get("/courses/semester_2026_1/stats")
        assert r.status_code == 200
        data = r.json()
        assert "total_sections" in data
        assert "unique_initials" in data
        assert data["semester"] == "semester_2026_1"
        assert data["total_sections"] == 4

    def test_stats_free_tier_forbidden(self, client):
        """Simulate a free-tier key by overriding the API key dependency."""
        from app.deps import get_api_key
        from app.main import app

        app.dependency_overrides[get_api_key] = lambda: ("free_key", "free", {})
        try:
            r = client.get("/courses/semester_2026_1/stats")
        finally:
            app.dependency_overrides.pop(get_api_key, None)
        assert r.status_code == 403


class TestStreaming:
    def test_stream_requires_pro(self, client):
        """In DEBUG mode (enterprise), streaming should work."""
        r = client.get("/courses/semester_2026_1/stream")
        assert r.status_code == 200
        lines = r.text.strip().split("\n")
        assert len(lines) == 4  # 4 sample rows
        for line in lines:
            obj = json.loads(line)
            assert "id" in obj
            assert "initials" in obj

    def test_stream_free_tier_forbidden(self, client):
        from app.deps import get_api_key
        from app.main import app

        app.dependency_overrides[get_api_key] = lambda: ("free_key", "free", {})
        try:
            r = client.get("/courses/semester_2026_1/stream")
        finally:
            app.dependency_overrides.pop(get_api_key, None)
        assert r.status_code == 403


class TestAdminCourses:
    def test_update_status(self, client):
        r = client.get("/admin/courses/update-status")
        assert r.status_code == 200
        data = r.json()
        assert "interval_seconds" in data
        assert "is_checking" in data

    def test_update_frequency_change(self, client):
        r = client.post("/admin/courses/update-frequency?interval_seconds=3600")
        assert r.status_code == 200
        data = r.json()
        assert data["interval_seconds"] == 3600

    def test_update_frequency_minimum(self, client):
        r = client.post("/admin/courses/update-frequency?interval_seconds=30")
        # FastAPI Query ge=60 returns 422, which we convert to 422
        assert r.status_code in [400, 422]

    def test_trigger_update_check(self, client):
        """Mock the GitHub API call so no real network request is made."""
        with patch("app.course_updater.get_latest_releases", return_value=[]):
            r = client.post("/admin/courses/update-check")
        assert r.status_code == 200
        data = r.json()
        assert "updated" in data
        assert "message" in data
