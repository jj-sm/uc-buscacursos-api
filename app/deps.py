from typing import Optional
from fastapi import Security, HTTPException, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from .auth_db import get_auth_db
from .auth_models import APIKey, TIER_CONFIG
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from collections import defaultdict

load_dotenv()

DEBUG = os.getenv("DEBUG", "0") == "1"

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Simple in-memory rate limiting tracker
# Format: {api_key: {"requests": [timestamp1, timestamp2, ...], "tier": "free"}}
_rate_limit_tracker = defaultdict(lambda: {"requests": [], "tier": None})
_WINDOW_SIZE = 1  # 1 second window


def _cleanup_old_requests(api_key: str, current_time: datetime):
    """Remove requests older than the window size"""
    cutoff_time = current_time - timedelta(seconds=_WINDOW_SIZE)
    tracker = _rate_limit_tracker[api_key]
    tracker["requests"] = [
        req_time for req_time in tracker["requests"]
        if req_time > cutoff_time
    ]


def _check_rate_limit(api_key: str, tier: str) -> bool:
    """
    Check if the API key has exceeded its rate limit.
    Returns True if the request is allowed, False if rate limited.
    """
    tier_config = TIER_CONFIG.get(tier)
    if not tier_config or tier_config["requests_per_second"] is None:
        # Enterprise tier or unlimited
        return True
    
    current_time = datetime.utcnow()
    tracker = _rate_limit_tracker[api_key]
    tracker["tier"] = tier
    
    # Cleanup old requests
    _cleanup_old_requests(api_key, current_time)
    
    # Check if we're under the limit
    limit = tier_config["requests_per_second"]
    if len(tracker["requests"]) >= limit:
        return False
    
    # Add current request
    tracker["requests"].append(current_time)
    return True


def get_api_key(api_key: Optional[str] = Security(api_key_header),
                db: Session = Depends(get_auth_db)) -> tuple:
    """
    Validates API key and checks rate limits.
    Returns tuple of (api_key, tier, limit_info)
    """
    if DEBUG:
        return api_key or "debug", "enterprise", {"limit": None, "remaining": None}

    if not api_key:
        raise HTTPException(status_code=403, detail="Not authorized. Missing API Key")

    key_obj = db.query(APIKey).filter_by(key=api_key, active=True).first()
    if not key_obj:
        raise HTTPException(status_code=403, detail="Invalid or inactive API Key")
    
    # Check rate limit
    tier = key_obj.tier or "free"
    if not _check_rate_limit(api_key, tier):
        tier_config = TIER_CONFIG[tier]
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Tier: {tier_config['name']} "
                   f"allows {tier_config['requests_per_second']} req/s"
        )
    
    # Get remaining requests in this window
    tracker = _rate_limit_tracker[api_key]
    tier_config = TIER_CONFIG[tier]
    remaining = (tier_config["requests_per_second"] - len(tracker["requests"])
                 if tier_config["requests_per_second"] else None)
    
    limit_info = {
        "tier": tier,
        "limit": tier_config["requests_per_second"],
        "remaining": remaining,
        "reset_in_seconds": _WINDOW_SIZE
    }
    
    return api_key, tier, limit_info

