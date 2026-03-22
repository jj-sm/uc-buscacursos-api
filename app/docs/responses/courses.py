"""OpenAPI response examples for the /courses endpoints."""

# ── /courses/semesters ─────────────────────────────────────────────────────────
GET_SEMESTERS = {
    200: {
        "description": "List of available semester table names",
        "content": {
            "application/json": {
                "example": {
                    "semesters": ["semester_2025_2", "semester_2026_1"],
                    "count": 2,
                }
            }
        },
    },
}

# ── /courses/{semester}/search ─────────────────────────────────────────────────
GET_SEARCH = {
    200: {
        "description": "Paginated search results",
        "content": {
            "application/json": {
                "example": {
                    "data": [
                        {
                            "id": "IIC2233-1",
                            "initials": "IIC2233",
                            "section": 1,
                            "nrc": "12345",
                            "name": "Programación Avanzada",
                            "credits": 10,
                            "req": "IIC1103",
                            "conn": None,
                            "restr": None,
                            "equiv": None,
                            "program": "Ingeniería Civil",
                            "school": "Ingeniería",
                            "area": "Ciencias de la Computación",
                            "category": "RE",
                            "teachers": "Nombre Apellido",
                            "schedule_json": '{"LUNES": ["10:00-11:30"]}',
                            "format": "Presencial",
                            "campus": "San Joaquín",
                            "is_english": 0,
                            "is_removable": 1,
                            "is_special": 0,
                            "total_quota": 40,
                            "quota_json": None,
                            "updated_at": "2025-07-01T12:00:00",
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "page_size": 20,
                    "pages": 1,
                }
            }
        },
    },
    404: {
        "description": "Semester not found",
        "content": {"application/json": {"example": {"detail": "Semester 'semester_2099_1' not found"}}},
    },
}

# ── /courses/{semester}/list ───────────────────────────────────────────────────
GET_LIST = GET_SEARCH

# ── /courses/{semester}/course/{id} ───────────────────────────────────────────
GET_COURSE_BY_ID = {
    200: {
        "description": "Single course record",
        "content": {
            "application/json": {
                "example": {
                    "id": "IIC2233-1",
                    "initials": "IIC2233",
                    "section": 1,
                    "nrc": "12345",
                    "name": "Programación Avanzada",
                    "credits": 10,
                    "req": "IIC1103",
                    "conn": None,
                    "restr": None,
                    "equiv": None,
                    "program": "Ingeniería Civil",
                    "school": "Ingeniería",
                    "area": "Ciencias de la Computación",
                    "category": "RE",
                    "teachers": "Nombre Apellido",
                    "schedule_json": '{"LUNES": ["10:00-11:30"]}',
                    "format": "Presencial",
                    "campus": "San Joaquín",
                    "is_english": 0,
                    "is_removable": 1,
                    "is_special": 0,
                    "total_quota": 40,
                    "quota_json": None,
                    "updated_at": "2025-07-01T12:00:00",
                }
            }
        },
    },
    404: {
        "description": "Course not found",
        "content": {"application/json": {"example": {"detail": "Course 'IIC2233-1' not found"}}},
    },
}

# ── /courses/{semester}/nrc/{nrc} ─────────────────────────────────────────────
GET_COURSE_BY_NRC = GET_COURSE_BY_ID

# ── /courses/{semester}/initials/{initials} ────────────────────────────────────
GET_COURSES_BY_INITIALS = {
    200: {
        "description": "All sections for a given course initials",
        "content": {
            "application/json": {
                "example": {
                    "initials": "IIC2233",
                    "sections": [
                        {"id": "IIC2233-1", "section": 1, "nrc": "12345", "teachers": "Nombre Apellido"},
                        {"id": "IIC2233-2", "section": 2, "nrc": "12346", "teachers": "Otro Docente"},
                    ],
                    "count": 2,
                }
            }
        },
    },
    404: {"description": "Course initials not found"},
}

# ── /courses/{semester}/stats ──────────────────────────────────────────────────
GET_STATS = {
    200: {
        "description": "Semester statistics (Premium+ tier required)",
        "content": {
            "application/json": {
                "example": {
                    "semester": "semester_2026_1",
                    "total_courses": 4200,
                    "total_sections": 8900,
                    "unique_initials": 1500,
                    "schools": 14,
                    "campuses": 4,
                    "formats": ["Presencial", "Online", "Híbrido"],
                    "english_courses": 312,
                    "avg_credits": 10.4,
                    "avg_quota": 38.2,
                }
            }
        },
    },
    403: {
        "description": "Insufficient tier (Premium or Enterprise required)",
        "content": {"application/json": {"example": {"detail": "Stats require Premium tier or above"}}},
    },
}

# ── /courses/{semester}/stream ─────────────────────────────────────────────────
GET_STREAM = {
    200: {
        "description": (
            "Streaming NDJSON of all courses (Pro tier or above required). "
            "Each line is a JSON object representing one course row."
        ),
        "content": {
            "application/x-ndjson": {
                "example": (
                    '{"id":"IIC2233-1","initials":"IIC2233","section":1,...}\n'
                    '{"id":"IIC2233-2","initials":"IIC2233","section":2,...}\n'
                )
            }
        },
    },
    403: {
        "description": "Insufficient tier (Pro or above required)",
        "content": {"application/json": {"example": {"detail": "Streaming requires Pro tier or above"}}},
    },
}

# ── metadata lists ─────────────────────────────────────────────────────────────
GET_METADATA_LIST = {
    200: {
        "description": "Sorted list of distinct values for the requested field",
        "content": {
            "application/json": {
                "example": {"values": ["Ingeniería", "Ciencias", "Letras"], "count": 3}
            }
        },
    },
}
