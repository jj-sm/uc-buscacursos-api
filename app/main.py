import os
import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.middleware.cors import CORSMiddleware
from .routers import (admin, airports, template, courses, admin_courses)
from .logging_middleware import RequestLoggerMiddleware
from .course_updater import periodic_course_updater
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

URL_PREFIX = os.getenv("URL_PREFIX", "").rstrip("/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup – launch background courses updater
    task = asyncio.create_task(periodic_course_updater())
    yield
    # Shutdown – cancel background task gracefully
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="UC BuscaCursos API",
    version="2.0.0",
    description=(
        "API for querying UC BuscaCursos course data from multiple semesters. "
        "Features tier-based authentication, rate limiting, streaming responses, "
        "and automatic semester database updates from jj-sm/buscacursos-dl-jj-sm."
    ),
    lifespan=lifespan
)
app.root_path = URL_PREFIX
app.add_middleware(RequestLoggerMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path("app/static")
if static_dir.exists() and static_dir.is_dir():
    app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request data"},
    )


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=(
            "UC BuscaCursos API – query course data across semesters. "
            "Authenticate using the `X-API-Key` header.  "
            "Available tiers: Free (10 req/s), Pro (100 req/s), "
            "Premium (1 000 req/s, stats access), "
            "Enterprise (unlimited, all features)."
        ),
        routes=app.routes,
    )

    # Add custom 403 response and remove 422
    for path in openapi_schema["paths"].values():
        for method in path.values():
            responses = method.get("responses", {})

            # Remove 422 if exists
            responses.pop("422", None)

            # Add custom 403 and 429
            responses["403"] = {
                "description": "Not authorized - missing or invalid API key",
                "content": {
                    "application/json": {
                        "example": {"detail": "Invalid or inactive API Key"}
                    }
                },
            }
            responses["429"] = {
                "description": "Rate limit exceeded for your tier",
                "content": {
                    "application/json": {
                        "example": {"detail": "Rate limit exceeded. Tier: Free allows 10 req/s"}
                    }
                },
            }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/health", tags=["System"], include_in_schema=True)
def health_check():
    """System health check endpoint"""
    return {"status": "healthy"}


# Root endpoint
@app.get("/", tags=["System"], include_in_schema=True)
def root():
    """API information and available endpoints"""
    return {
        "title": "UC BuscaCursos API",
        "name": "UC BuscaCursos API",
        "version": "2.0.0",
        "description": "API for UC BuscaCursos course data with tier-based authentication",
        "docs": "/docs",
        "authentication": "X-API-Key header required",
        "tiers": {
            "free": "10 req/s – search, list, retrieve",
            "pro": "100 req/s – + streaming (NDJSON)",
            "premium": "1000 req/s – + semester statistics",
            "enterprise": "unlimited"
        }
    }


# Routers
app.include_router(admin.router, prefix="/admin", tags=["Admin"], include_in_schema=True)
app.include_router(admin_courses.router, prefix="/admin/courses", tags=["Admin – Courses"], include_in_schema=True)
app.include_router(courses.router, prefix="/courses", tags=["Courses"], include_in_schema=True)
app.include_router(template.router, prefix="/template", tags=["Template Example"], include_in_schema=True)
app.include_router(airports.router, prefix="/airports", tags=["Airports Example"], include_in_schema=True)
