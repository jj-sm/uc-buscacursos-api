"""
API Rate Limiting and Tier Management Configuration

This module defines the tier system and utilities for managing API access.
Tiers control how many requests per second each API key can make.
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class APITier(str, Enum):
    """Enumeration of available API tiers"""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


# Tier Configuration
# Rates are in requests per second (req/s)
TIER_LIMITS: Dict[str, Dict[str, Any]] = {
    APITier.FREE.value: {
        "name": "Free",
        "requests_per_second": 10,
        "max_burst": 20,
        "description": "Free tier with basic rate limiting. Good for development and testing.",
        "features": ["Basic API access", "Standard support"],
    },
    APITier.PRO.value: {
        "name": "Pro",
        "requests_per_second": 100,
        "max_burst": 200,
        "description": "Professional tier with higher rate limits. Suitable for small production use.",
        "features": ["100 req/s", "Priority support", "SLA available"],
    },
    APITier.PREMIUM.value: {
        "name": "Premium",
        "requests_per_second": 1000,
        "max_burst": 2000,
        "description": "Premium tier for demanding applications",
        "features": ["1000 req/s", "24/7 support", "Guaranteed SLA"],
    },
    APITier.ENTERPRISE.value: {
        "name": "Enterprise",
        "requests_per_second": None,  # None means unlimited
        "max_burst": None,
        "description": "Enterprise tier with custom limits and dedicated support",
        "features": ["Custom rate limits", "Dedicated account manager", "Custom SLA"],
    }
}


def get_tier_limits(tier: str) -> Optional[Dict[str, Any]]:
    """Get the rate limit configuration for a given tier"""
    return TIER_LIMITS.get(tier.lower())


def is_rate_limited(requests_in_window: int, tier: str) -> bool:
    """
    Check if the current request count exceeds the tier limit.
    
    Args:
        requests_in_window: Number of requests in current time window
        tier: API tier string
    
    Returns:
        True if rate limited, False if request is allowed
    """
    config = get_tier_limits(tier)
    if not config or config["requests_per_second"] is None:
        return False  # Unlimited tier
    
    return requests_in_window >= config["requests_per_second"]


def get_retry_after(tier: str) -> int:
    """Get recommended retry-after seconds for a given tier"""
    config = get_tier_limits(tier)
    if not config:
        return 60
    
    # Recommend retry after the time window + buffer
    return max(1, config["requests_per_second"] // 10) if config["requests_per_second"] else 60


def format_tier_info(tier: str) -> Dict[str, Any]:
    """Format tier information for display"""
    config = get_tier_limits(tier)
    if not config:
        return {"error": "Invalid tier"}
    
    return {
        "tier": tier.upper(),
        "name": config["name"],
        "requests_per_second": config["requests_per_second"],
        "description": config["description"],
        "features": config["features"],
    }


# Example usage in your API:
# 
# from .rate_limiter import APITier, TIER_LIMITS, format_tier_info
# from fastapi import HTTPException
#
# @app.get("/tier-info")
# async def get_tier_info(api_key=Depends(get_api_key)):
#     tier = get_tier_from_key(api_key)
#     return format_tier_info(tier)
#
# @app.get("/limits")
# async def get_limits():
#     """Get all available tiers and their limits"""
#     return {tier: info["requests_per_second"] for tier, info in TIER_LIMITS.items()}
