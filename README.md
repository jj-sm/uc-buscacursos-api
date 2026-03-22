# Universal API Template

A modern, scalable RESTful API template built with FastAPI. This template provides a production-ready foundation for building APIs with tier-based authentication, rate limiting, and comprehensive documentation.

## Features

- **Tier-Based Authentication**: 4 API tiers with different rate limits (Free/Pro/Premium/Enterprise)
- **Rate Limiting**: Sliding-window rate limiter with per-tier configuration
  - Free: 10 requests/second
  - Pro: 100 requests/second
  - Premium: 1,000 requests/second
  - Enterprise: Unlimited
- **Admin Management**: API key lifecycle management and statistics
- **API Key Authentication**: Secure API key-based authentication
- **Database Integration**: SQLite/PostgreSQL support with SQLAlchemy ORM
- **RESTful Design**: Clean, well-documented REST API endpoints
- **Interactive Documentation**: Auto-generated Swagger UI and ReDoc
- **Docker Support**: Containerized deployment with Docker and docker-compose
- **Example Routers**: Template and airports routers with 8+ endpoint patterns
- **Comprehensive Documentation**: Getting started guides, quick reference, and migration guides

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

### Getting Started

- **[DEVELOPER_QUICKSTART.md](DEVELOPER_QUICKSTART.md)** - 5-minute start guide (recommended first read)
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Quick lookup for common tasks
- **[API_TEMPLATE_GUIDE.md](API_TEMPLATE_GUIDE.md)** - Complete setup and usage guide
- **[ROUTER_MIGRATION_GUIDE.md](ROUTER_MIGRATION_GUIDE.md)** - Guide for creating and registering new routers

### Project Structure

- **Core System**:
  - `app/main.py` - FastAPI application setup
  - `app/auth_models.py` - Tier-based API key models
  - `app/deps.py` - Authentication and rate limiting
  - `app/db.py` & `app/auth_db.py` - Database connections

- **routers/**:
  - `admin.py` - API key management and statistics
  - `template.py` - 8 endpoint pattern examples (start here!)
  - `airports.py` - Real-world example integration

- **helpers/**:
  - `data_io.py` - Data transformation utilities

## Usage

### Creating an API Key

Access the admin panel at `http://localhost:8000/api/admin/` to create API keys with different tiers.

### Making API Requests

```bash
# Basic request with API key
curl -H "X-API-Key: your-api-key" \
     http://localhost:8000/api/template/resources

# Response includes rate limit info
# X-RateLimit-Limit: 10
# X-RateLimit-Remaining: 9
# X-RateLimit-Reset: 59
```

### Understanding Rate Limits

Rate limits are enforced per API key and tier:

| Tier | Requests/Second | Max Burst | Cost |
|------|-----------------|-----------|------|
| Free | 10 | 20 | Free |
| Pro | 100 | 200 | $9/mo |
| Premium | 1,000 | 2,000 | $99/mo |
| Enterprise | Unlimited | N/A | Custom |

When you exceed rate limits, you'll receive a 429 response with `Retry-After` header.

### Building a Custom Router

1. **Create** your router file in `app/routers/my_router.py`
2. **Follow** the patterns in `routers/template.py` (8 examples provided)
3. **Register** in `app/main.py`:
   ```python
   from .routers import admin, airports, template, my_router
   
   app.include_router(my_router.router, prefix="/api/my", tags=["My Router"])
   ```
4. **Test** at `http://localhost:8000/docs`

### Authentication

All API endpoints require authentication via API key. Include your API key in the request header:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/airports/
```

## API Endpoints

### Admin Panel

Access the admin panel to manage API keys:

```bash
# View admin dashboard
http://localhost:8000/api/admin/
```

### Template Router

8 example endpoint patterns for reference:

```bash
# List resources
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/template/resources

# Get specific resource
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/template/resources/123

# Search resources
curl -H "X-API-Key: your-api-key" "http://localhost:8000/api/template/resources/search?q=test"

# Create resource (requires Pro tier or higher)
curl -X POST -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"name":"New Resource"}' \
     http://localhost:8000/api/template/resources
```

### Airports Router

Real-world example of database integration:

```bash
# List all airports
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/airports/

# Get airport by code
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/airports/SKBO
```

## Configuration

Environment variables for configuration (see `.env.example`):

```bash
# Database
DATABASE_URL=sqlite:///./data/app.db
AUTH_DATABASE_URL=sqlite:///./data/auth.db

# Server
API_URL=0.0.0.0
API_PORT=8000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Logging
LOG_LEVEL=INFO
```

## Project Structure

```
uc-buscacursos-api/
├── app/
│   ├── main.py                 # FastAPI application setup
│   ├── auth_models.py          # Tier-based API key models
│   ├── auth_db.py              # Auth database connection
│   ├── db.py                   # Main database connection
│   ├── deps.py                 # Authentication & rate limiting
│   ├── generic_models.py       # Template data models
│   ├── models.py               # SQLAlchemy ORM models
│   ├── logging_middleware.py   # Request logging
│   ├── admin_key_manager.py    # API key lifecycle management
│   ├── rate_limiter.py         # Tier configuration & utilities
│   ├── helpers/
│   │   ├── __init__.py
│   │   └── data_io.py          # Data transformation utilities
│   └── routers/
│       ├── __init__.py
│       ├── admin.py            # API key management endpoints
│       ├── template.py         # 8 endpoint pattern examples
│       └── airports.py         # Real-world database example
├── data/                       # Data directory
├── docs/                       # Documentation
├── logs/                       # Application logs
├── test/                       # Test files
├── .env.example                # Environment template
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container configuration
├── docker-compose.yaml         # Multi-container setup
├── run.py                      # Application runner
├── DEVELOPER_QUICKSTART.md     # 5-minute start guide
├── QUICK_REFERENCE.md          # Quick lookup
├── API_TEMPLATE_GUIDE.md       # Complete guide
└── README.md                   # This file
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
- **Examples**: Check `routers/template.py` and `routers/airports.py`
- **Issues**: Report on GitHub issues tracker

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Version

**v1.0.0** - Universal API Template
