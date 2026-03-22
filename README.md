# UC BuscaCursos API

A FastAPI-based REST API for querying UC (Pontificia Universidad Católica de Chile) BuscaCursos course data. Courses are stored in a SQLite database with one table per semester and are automatically updated from the [`jj-sm/buscacursos-dl-jj-sm`](https://github.com/jj-sm/buscacursos-dl-jj-sm) releases.

## Test it

- **ReDocs**: visit the API Documentation here: [uc.api.jjsm.science/redoc](https://uc.api.jjsm.science/redoc)
- **Swagger UI**: visit the API Documentation here: [uc.api.jjsm.science/docs#](https://uc.api.jjsm.science/docs#)

> For testing, use this free tier key: `X-API-Key: i2bUXB2DBnP01tXA3vQCYjYNNHhAHIkjX25Bj63zkVc`, if you need to make more requests per second, contact me at [api@jjsm.science](mailto:api@jjsm.science). It won't have any cost, just need to control who access massively the API.

## Features

- **BuscaCursos Endpoints**: Search, list, retrieve, stream, and aggregate course data across semesters
- **Tier-Based Authentication**: 4 API tiers with different rate limits (Free/Pro/Premium/Enterprise)
- **Rate Limiting**: Sliding-window rate limiter with per-tier configuration
  - Free: 10 requests/second
  - Pro: 100 requests/second + NDJSON streaming
  - Premium: 1,000 requests/second + semester statistics
  - Enterprise: Unlimited
- **Streaming Responses**: Stream full semester datasets as NDJSON (Pro+)
- **Auto-Update**: Background task checks GitHub for new semester releases monthly (configurable)
- **Admin Management**: API key lifecycle, update-frequency control, manual update triggers
- **API Key Authentication**: Secure API key-based authentication via `X-API-Key` header
- **Interactive Documentation**: Auto-generated Swagger UI (`/docs`) and ReDoc (`/redoc`)

## Quick Start

### Prerequisites

- Python 3.8+
- SQLite 3.6+ (default) or PostgreSQL/MySQL for production
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jj-sm/uc-buscacursos-api.git
   cd uc-buscacursos-api
   ```

2. **Install dependencies:**
   ```bash
   ./scripts/setup.sh
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application:**
   ```bash
   ./scripts/run.sh
   ```

The API will be available at `http://localhost:8000`

### Docker Deployment

1. **Using docker-compose (recommended):**
   ```bash
   ./scripts/docker-up.sh
   ```

2. **Manual Docker build:**
   ```bash
   ./scripts/docker-build.sh universal-api:local
   docker run -p 8000:8000 universal-api:local
   ```

## Documentation

### Courses API Reference

- **[docs/COURSES_API.md](docs/COURSES_API.md)** – Full endpoint reference for BuscaCursos

### Interactive API Docs

Run the server and visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Project Structure

- **Core System**:
  - `app/main.py` - FastAPI application setup and lifespan (starts background updater)
  - `app/auth_models.py` - Tier-based API key models
  - `app/deps.py` - Authentication and rate limiting
  - `app/course_db.py` - Raw sqlite3 connection for dynamic semester tables
  - `app/course_updater.py` - Periodic GitHub release checker / DB merger

- **routers/**:
  - `courses.py` - All BuscaCursos endpoints (search, list, stream, stats, metadata)
  - `admin_courses.py` - Update frequency, status, and manual trigger endpoints
  - `admin.py` - API key management

## Usage

### Quick Start with BuscaCursos

1. Set up environment:
   ```bash
   cp .env.example .env
   # Set COURSES_DATABASE_URL, GITHUB_TOKEN (optional)
   ```

2. Run the server:
   ```bash
   ./scripts/run.sh
   ```

3. On first start the background task will check GitHub for the latest semester and download it automatically.

### Making API Requests

```bash
# List available semesters
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/courses/semesters

# Search courses
curl -H "X-API-Key: your-api-key" \
     "http://localhost:8000/courses/semester_2026_1/search?q=programacion&page_size=5"

# Get course by NRC
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/courses/semester_2026_1/nrc/12345

# Stream entire semester (Pro+)
curl -H "X-API-Key: your-pro-api-key" \
     http://localhost:8000/courses/semester_2026_1/stream

# Semester statistics (Premium+)
curl -H "X-API-Key: your-premium-api-key" \
     http://localhost:8000/courses/semester_2026_1/stats
```

### Admin: Update Management

```bash
# Check update status
curl -H "X-API-Key: admin-key" \
     http://localhost:8000/admin/courses/update-status

# Trigger immediate update check
curl -X POST -H "X-API-Key: admin-key" \
     http://localhost:8000/admin/courses/update-check

# Change update interval to 7 days
curl -X POST -H "X-API-Key: admin-key" \
     "http://localhost:8000/admin/courses/update-frequency?interval_seconds=604800"
```

### Understanding Rate Limits

Rate limits are enforced per API key and tier:

| Tier | Requests/Second | Features |
|------|-----------------|----------|
| Free | 10 | Search, list, retrieve |
| Pro | 100 | + NDJSON streaming |
| Premium | 1,000 | + Semester statistics |
| Enterprise | Unlimited | All features |

When you exceed rate limits, you'll receive a 429 response.

### Building a Custom Router

1. **Create** your router file in `app/routers/my_router.py`
2. **Follow** the patterns in `routers/template.py` (examples provided)
3. **Register** in `app/main.py`:
   ```python
   from .routers import admin, template, courses, my_router
   
   app.include_router(my_router.router, prefix="/api/my", tags=["My Router"])
   ```
4. **Test** at `http://localhost:8000/docs`

### Authentication

All API endpoints require authentication via API key. Include your API key in the request header:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/courses/semesters
```

## API Endpoints

### Courses (BuscaCursos)

See **[docs/COURSES_API.md](docs/COURSES_API.md)** for the full endpoint reference.

| Endpoint | Tier | Description |
|----------|------|-------------|
| `GET /courses/semesters` | Free | List available semesters |
| `GET /courses/{sem}/search` | Free | Search with filters + pagination |
| `GET /courses/{sem}/list` | Free | Paginated full list |
| `GET /courses/{sem}/course/{id}` | Free | Single course by composite ID |
| `GET /courses/{sem}/nrc/{nrc}` | Free | Single course by NRC |
| `GET /courses/{sem}/initials/{ini}` | Free | All sections by course initials |
| `GET /courses/{sem}/schools` | Free | Distinct schools |
| `GET /courses/{sem}/areas` | Free | Distinct areas |
| `GET /courses/{sem}/categories` | Free | Distinct categories |
| `GET /courses/{sem}/campuses` | Free | Distinct campuses |
| `GET /courses/{sem}/formats` | Free | Distinct formats |
| `GET /courses/{sem}/programs` | Free | Distinct programs |
| `GET /courses/{sem}/teachers` | Free | Distinct teachers |
| `GET /courses/{sem}/stream` | Pro+ | NDJSON streaming of all courses |
| `GET /courses/{sem}/stats` | Premium+ | Aggregated semester statistics |

### Admin – Courses Update

| Endpoint | Description |
|----------|-------------|
| `GET /admin/courses/update-status` | Current updater state |
| `POST /admin/courses/update-check` | Trigger immediate GitHub check |
| `POST /admin/courses/update-frequency` | Change check interval |

### Admin – API Keys

| Endpoint | Description |
|----------|-------------|
| `GET /admin/` | List admin endpoints |
| `POST /admin/keys` | Create API key |
| `GET /admin/keys/list` | List all API keys |
| `PATCH /admin/keys/{name}` | Deactivate API key |
| `GET /admin/authenticated` | Check authentication |

## Configuration

Environment variables for configuration (see `.env.example`):

```bash
# Courses database (buscacursos data)
COURSES_DATABASE_URL=sqlite:///./data/courses.sqlite
GITHUB_TOKEN=                          # optional, for release API
COURSES_UPDATE_INTERVAL_SECONDS=2592000 # 30 days

# Auth database
AUTH_DATABASE_URL=sqlite:///./auth_data/api_keys.db

# Server
API_URL=0.0.0.0
API_PORT=8000

# CORS
CORS_ORIGINS=*

# Debug (set 1 to skip auth)
DEBUG=0
```

## Project Structure

```
uc-buscacursos-api/
├── app/
│   ├── main.py                 # FastAPI app setup + background updater
│   ├── auth_models.py          # Tier-based API key models
│   ├── auth_db.py              # Auth database connection
│   ├── course_db.py            # Raw sqlite3 for semester tables
│   ├── course_updater.py       # GitHub release checker / DB merger
│   ├── deps.py                 # Authentication & rate limiting
│   ├── docs/responses/
│   │   └── courses.py          # OpenAPI response examples
│   └── routers/
│       ├── courses.py          # All BuscaCursos endpoints
│       ├── admin_courses.py    # Update management endpoints
│       └── admin.py            # API key management endpoints
├── data/                       # SQLite databases (gitignored)
├── docs/
│   └── COURSES_API.md          # Full endpoint reference
├── test/
│   ├── test_courses.py         # Courses endpoint tests
│   └── test_api_endpoints.py   # General API tests
└── .env.example                # Environment template
```

## Development

### Setup

```bash
# Setup project
./scripts/setup.sh

# Run development server with auto-reload
./scripts/run-dev.sh
```

### Creating Custom Endpoints

Follow the patterns in `routers/template.py`:

1. Define Pydantic models for request/response validation
2. Extract rate limit info from `get_api_key()` dependency
3. Implement business logic
4. Include appropriate error handling
5. Register router in `main.py`

See [ROUTER_MIGRATION_GUIDE.md](ROUTER_MIGRATION_GUIDE.md) for detailed examples.

### Testing

```bash
# Interactive docs
http://localhost:8000/docs

# ReDoc documentation
http://localhost:8000/redoc

# Health check
./scripts/verify.sh
```

## Tier Configuration

Modify tier limits by editing `TIER_CONFIG` in `app/auth_models.py`:

```python
TIER_CONFIG = {
    "free": {
        "requests_per_second": 10,
        "max_burst": 20,
        "description": "Free tier",
        "features": ["read-only access"]
    },
    "pro": {
        "requests_per_second": 100,
        "max_burst": 200,
        "description": "Professional tier",
        "features": ["read-write access", "advanced analytics"]
    },
    # ... more tiers
}
```

## Support & Resources

- **Quick Start**: Read [DEVELOPER_QUICKSTART.md](DEVELOPER_QUICKSTART.md)
- **Complete Setup**: See [API_TEMPLATE_GUIDE.md](API_TEMPLATE_GUIDE.md)
- **API Docs**: Run the server and visit `http://localhost:8000/docs`
- **Examples**: Check `routers/template.py` and `routers/courses.py`
- **Issues**: Report on GitHub issues tracker

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Version

**v1.0.0** - Universal API Template
