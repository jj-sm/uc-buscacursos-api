# UC BuscaCursos API – Endpoint Reference

This document describes all available endpoints for the UC BuscaCursos API. The API serves course data scraped from UC's BuscaCursos system, organised by semester, and updated automatically from the [`jj-sm/buscacursos-dl-jj-sm`](https://github.com/jj-sm/buscacursos-dl-jj-sm) GitHub releases.

---

## Authentication

Every endpoint (except `/health` and `/`) requires an **API key** supplied via the `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

### Tiers

| Tier | Rate limit | Streaming | Stats | Notes |
|------|-----------|-----------|-------|-------|
| **Free** | 10 req/s | ✗ | ✗ | Default |
| **Pro** | 100 req/s | ✓ | ✗ | NDJSON streaming |
| **Premium** | 1 000 req/s | ✓ | ✓ | Full analytics |
| **Enterprise** | Unlimited | ✓ | ✓ | Custom SLA |

---

## Courses Endpoints

### `GET /courses/semesters`

List all semester tables available in the database.

**Response**
```json
{
  "semesters": ["semester_2025_2", "semester_2026_1"],
  "count": 2
}
```

---

### `GET /courses/{semester}/search`

Search courses within a semester using one or more filters. All parameters are optional and can be combined.

**Path parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| `semester` | `string` | Semester name, e.g. `semester_2026_1` |

**Query parameters**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | `string` | Free-text search across `name`, `initials`, and `teachers` |
| `initials` | `string` | Exact match on course initials (case-insensitive) |
| `name` | `string` | Partial match on course name |
| `teacher` | `string` | Partial match on teacher name |
| `school` | `string` | Exact match on school |
| `area` | `string` | Exact match on area |
| `category` | `string` | Exact match on category |
| `campus` | `string` | Exact match on campus |
| `format` | `string` | Exact match on delivery format |
| `credits` | `integer` | Exact number of credits |
| `is_english` | `boolean` | Filter English-language courses |
| `is_special` | `boolean` | Filter special courses |
| `page` | `integer` | Page number (default: 1) |
| `page_size` | `integer` | Results per page (default: 20, max: 200) |

**Response**
```json
{
  "data": [ /* array of course objects */ ],
  "total": 142,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

---

### `GET /courses/{semester}/list`

Return all courses in the semester with pagination.

**Query parameters**: `page`, `page_size` (same as `/search`)

**Response**: same schema as `/search`

---

### `GET /courses/{semester}/course/{id}`

Retrieve a single course by its composite primary key.

**Path parameters**
| Parameter | Description |
|-----------|-------------|
| `semester` | Semester name |
| `id` | Composite ID, e.g. `IIC2233-1` |

**Response**: single course object or `404`.

---

### `GET /courses/{semester}/nrc/{nrc}`

Retrieve a single course section by NRC (NRC is unique within a semester).

**Response**: single course object or `404`.

---

### `GET /courses/{semester}/initials/{initials}`

Return all sections of a course by its initials.

**Response**
```json
{
  "initials": "IIC2233",
  "semester": "semester_2026_1",
  "sections": [ /* array of course objects */ ],
  "count": 4
}
```

---

### `GET /courses/{semester}/stats` *(Premium+)*

Aggregated statistics for a semester. Requires **Premium** tier or above.

**Response**
```json
{
  "semester": "semester_2026_1",
  "total_sections": 8900,
  "unique_initials": 1500,
  "schools": 14,
  "campuses": 4,
  "formats": ["Presencial", "Online", "Híbrido"],
  "english_courses": 312,
  "avg_credits": 10.4,
  "avg_quota": 38.2
}
```

---

### `GET /courses/{semester}/stream` *(Pro+)*

Stream all courses in the semester as **Newline-Delimited JSON (NDJSON)**. Each line is a complete, self-contained JSON object. Requires **Pro** tier or above.

**Response**: `Content-Type: application/x-ndjson`

```
{"id":"IIC2233-1","initials":"IIC2233","section":1,...}
{"id":"IIC2233-2","initials":"IIC2233","section":2,...}
```

---

## Metadata Endpoints

All metadata endpoints follow the same response schema:

```json
{ "values": ["value1", "value2"], "count": 2 }
```

| Endpoint | Description |
|----------|-------------|
| `GET /courses/{semester}/schools` | Distinct school names |
| `GET /courses/{semester}/areas` | Distinct academic areas |
| `GET /courses/{semester}/categories` | Distinct category codes (RE, OFG, EL, …) |
| `GET /courses/{semester}/campuses` | Distinct campus names |
| `GET /courses/{semester}/formats` | Distinct delivery formats |
| `GET /courses/{semester}/programs` | Distinct academic programs |
| `GET /courses/{semester}/teachers` | Distinct teacher strings (as stored) |

---

## Admin – Courses Update Endpoints

These endpoints manage the automatic semester database updater.

### `GET /admin/courses/update-status`

Returns the current state of the background updater.

**Response**
```json
{
  "interval_seconds": 2592000,
  "interval_description": "30 day(s)",
  "last_check": "2026-03-01T12:00:00",
  "last_result": "Database is already up to date.",
  "is_checking": false
}
```

---

### `POST /admin/courses/update-check`

Triggers an immediate check against the upstream `jj-sm/buscacursos-dl-jj-sm` GitHub releases. Any new semester data found is downloaded and merged into the local database.

**Response**
```json
{
  "updated": true,
  "new_semesters": ["semester_2026_2"],
  "message": "Merged new semester(s): semester_2026_2"
}
```

---

### `POST /admin/courses/update-frequency`

Changes how often the background task checks for new semesters.

**Query parameters**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `interval_seconds` | `integer` | `2592000` | New interval (minimum: 60 s) |

**Response**
```json
{
  "interval_seconds": 86400,
  "interval_description": "1 day(s)",
  "message": "Update interval changed to 86400 seconds (1 day(s))"
}
```

---

## Course Object Schema

Every course row has the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `id` | `string` | Composite primary key, e.g. `IIC2233-1` |
| `initials` | `string` | Course code, e.g. `IIC2233` |
| `section` | `integer` | Section number |
| `nrc` | `string` | NRC (unique registration code within semester) |
| `name` | `string` | Course name |
| `credits` | `integer` | Number of credits |
| `req` | `string` | Prerequisites |
| `conn` | `string` | Co-requisites |
| `restr` | `string` | Restrictions |
| `equiv` | `string` | Equivalent courses |
| `program` | `string` | Academic program |
| `school` | `string` | School / Faculty |
| `area` | `string` | Academic area |
| `category` | `string` | Category (RE, OFG, EL, …) |
| `teachers` | `string` | Teacher name(s) |
| `schedule_json` | `string` | JSON-encoded schedule |
| `format` | `string` | Delivery format |
| `campus` | `string` | Campus |
| `is_english` | `integer` | `1` if taught in English |
| `is_removable` | `integer` | `1` if retirable |
| `is_special` | `integer` | `1` if special section |
| `total_quota` | `integer` | Total enrollment quota |
| `quota_json` | `string` | JSON-encoded quota breakdown |
| `updated_at` | `datetime` | Last update timestamp |

---

## Error Responses

| Status | Meaning |
|--------|---------|
| `403` | Missing/invalid API key, or tier too low for the requested endpoint |
| `404` | Semester or course not found |
| `429` | Rate limit exceeded |

---

## Automatic Update Logic

The API automatically checks for new semesters on a configurable interval (default: every **30 days**). The check:

1. Fetches the most recent releases from `jj-sm/buscacursos-dl-jj-sm`.
2. Converts each release tag to a table name (e.g. `2026_2` → `semester_2026_2`).
3. If the table does not yet exist in the local database, downloads the release asset and merges the new table(s) into the existing DB.
4. If the semester is already present, no download occurs.

Set `GITHUB_TOKEN` in your environment to avoid GitHub API rate limits.
