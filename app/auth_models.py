from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime
from enum import Enum

Base = declarative_base()


class TierEnum(str, Enum):
    """API key tier levels with rate limiting"""
    FREE = "free"           # 10 req/s
    PRO = "pro"             # 100 req/s
    PREMIUM = "premium"     # 1000 req/s
    ENTERPRISE = "enterprise"  # unlimited


class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    name = Column(String)
    tier = Column(String, default=TierEnum.FREE.value)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Metadata
    owner_name = Column(String, nullable=True)
    owner_email = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    # Rate limit tracking (optional, for monitoring)
    last_reset = Column(DateTime, default=datetime.utcnow)
    requests_count = Column(Integer, default=0)


# Tier configuration mapping
TIER_CONFIG = {
    TierEnum.FREE.value: {
        "name": "Free",
        "requests_per_second": 10,
        "max_burst": 20,
        "description": "Free tier with basic rate limiting"
    },
    TierEnum.PRO.value: {
        "name": "Pro",
        "requests_per_second": 100,
        "max_burst": 200,
        "description": "Professional tier with higher rate limits"
    },
    TierEnum.PREMIUM.value: {
        "name": "Premium",
        "requests_per_second": 1000,
        "max_burst": 2000,
        "description": "Premium tier with high rate limits"
    },
    TierEnum.ENTERPRISE.value: {
        "name": "Enterprise",
        "requests_per_second": None,  # Unlimited
        "max_burst": None,
        "description": "Enterprise tier with custom limits"
    }
}
