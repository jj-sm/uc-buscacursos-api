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
from .routers import (admin, airports, template)
from .logging_middleware import RequestLoggerMiddleware
from dotenv import load_dotenv
from contextlib import asynccontextmanager

load_dotenv()

URL_PREFIX = os.getenv("URL_PREFIX", "").rstrip("/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Universal API",
    version="1.0.0",
    description="A modern, scalable API template with tier-based authentication and rate limiting",
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
        description="Universal API Documentation with tier-based rate limiting. "
                    "Authenticate using X-API-Key header. Available tiers: Free (10 req/s), "
                    "Pro (100 req/s), Premium (1000 req/s), Enterprise (unlimited).",
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


# Health check endpoint
@app.get("/health", tags=["System"], include_in_schema=True)
def health_check():
    """System health check endpoint"""
    return {"status": "healthy"}


# Root endpoint
@app.get("/", tags=["System"], include_in_schema=True)
def root():
    """API information and available endpoints"""
    return {
        "name": "Universal API",
        "version": "1.0.0",
        "description": "A modern, scalable API template with tier-based authentication",
        "docs": "/docs",
        "authentication": "X-API-Key header required",
        "tiers": {
            "free": "10 req/s",
            "pro": "100 req/s",
            "premium": "1000 req/s",
            "enterprise": "unlimited"
        }
    }


# Routers - Example implementations
app.include_router(admin.router, prefix="/admin", tags=["Admin"], include_in_schema=True)
app.include_router(template.router, prefix="/template", tags=["Template Example"], include_in_schema=True)
app.include_router(airports.router, prefix="/airports", tags=["Airports Example"], include_in_schema=True)
