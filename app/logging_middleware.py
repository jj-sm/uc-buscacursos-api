import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
from .auth_db import SessionLocal
from .auth_models import APIKey

logger = logging.getLogger("airac_logger")
handler = logging.FileHandler("logs/airac_requests.log")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get start time
        start_time = time.time()

        # Get API key from header
        api_key = request.headers.get("X-API-Key", "")

        # Try to get API key name from DB (optional: skip if DB unavailable)
        key_name = ""
        if api_key:
            try:
                db: Session = SessionLocal()
                key_obj = db.query(APIKey).filter_by(key=api_key).first()
                key_name = key_obj.name if key_obj else ""
                db.close()
            except Exception:
                pass

        # Get client IP
        client_ip = request.client.host if request.client else ""

        # Get path and method
        path = request.url.path
        method = request.method

        # Get query params
        query = str(request.url.query)

        # Run the request and get response size
        response: Response = await call_next(request)
        process_time = time.time() - start_time

        # Response size: try to get from content-length, else calculate
        resp_size = response.headers.get("content-length")
        if resp_size is None and hasattr(response, "body_iterator"):
            # Streaming response, can't know size
            resp_size = "streaming"
        elif resp_size is None:
            # Try to get size from body if possible (not always possible)
            try:
                resp_size = str(len(response.body))
            except Exception:
                resp_size = "unknown"

        # Log the data
        logger.info(
            f"APIKEY={api_key} NAME={key_name} IP={client_ip} "
            f"{method} {path}?{query} RESP_SIZE={resp_size} TIME={process_time:.3f}s"
        )

        return response
