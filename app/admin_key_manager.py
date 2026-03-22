"""
Admin management utilities for API keys and rates

This module provides utilities for managing API keys, viewing statistics,
and administering the rate limiting system.
"""

from sqlalchemy.orm import Session
from .auth_models import APIKey, TierEnum, TIER_CONFIG
from typing import List, Dict, Any, Optional
from datetime import datetime


class AdminKeyManager:
    """Manage API keys and tier assignments"""
    
    @staticmethod
    def create_key(
        db: Session,
        name: str,
        tier: str = TierEnum.FREE.value,
        owner_name: Optional[str] = None,
        owner_email: Optional[str] = None,
        description: Optional[str] = None,
        key: Optional[str] = None
    ) -> APIKey:
        """Create a new API key"""
        if key is None:
            import secrets
            key = secrets.token_urlsafe(32)
        
        api_key = APIKey(
            key=key,
            name=name,
            tier=tier,
            owner_name=owner_name,
            owner_email=owner_email,
            description=description,
        )
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        return api_key
    
    @staticmethod
    def get_key_by_value(db: Session, key: str) -> APIKey:
        """Retrieve an API key by its value"""
        return db.query(APIKey).filter_by(key=key).first()
    
    @staticmethod
    def list_keys(db: Session, active_only: bool = False) -> List[APIKey]:
        """List all API keys"""
        query = db.query(APIKey)
        if active_only:
            query = query.filter_by(active=True)
        return query.all()
    
    @staticmethod
    def update_tier(db: Session, key_id: int, new_tier: str) -> APIKey:
        """Change an API key's tier"""
        api_key = db.query(APIKey).filter_by(id=key_id).first()
        if api_key:
            setattr(api_key, "tier", new_tier)
            setattr(api_key, "last_reset", datetime.utcnow())
            setattr(api_key, "requests_count", 0)
            db.commit()
            db.refresh(api_key)
        return api_key
    
    @staticmethod
    def deactivate_key(db: Session, key_id: int) -> APIKey:
        """Deactivate an API key"""
        api_key = db.query(APIKey).filter_by(id=key_id).first()
        if api_key:
            setattr(api_key, "active", False)
            db.commit()
            db.refresh(api_key)
        return api_key
    
    @staticmethod
    def reactivate_key(db: Session, key_id: int) -> APIKey:
        """Reactivate an API key"""
        api_key = db.query(APIKey).filter_by(id=key_id).first()
        if api_key:
            setattr(api_key, "active", True)
            db.commit()
            db.refresh(api_key)
        return api_key
    
    @staticmethod
    def get_key_info(db: Session, key_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about an API key"""
        api_key = db.query(APIKey).filter_by(id=key_id).first()
        if not api_key:
            return None
        
        tier_value = str(getattr(api_key, "tier", ""))
        tier_config = TIER_CONFIG.get(tier_value, {})
        
        return {
            "id": api_key.id,
            "name": api_key.name,
            "owner": api_key.owner_name,
            "email": api_key.owner_email,
            "tier": tier_value,
            "tier_name": tier_config.get("name"),
            "tier_limit": tier_config.get("requests_per_second"),
            "description": api_key.description,
            "active": api_key.active,
            "created_at": api_key.created_at.isoformat(),
            "requests_today": api_key.requests_count,
        }
    
    @staticmethod
    def get_usage_summary(db: Session) -> Dict[str, Any]:
        """Get summary of all API keys and their usage"""
        all_keys = db.query(APIKey).all()
        by_tier = {}
        
        for tier in TierEnum:
            tier_keys = [k for k in all_keys if str(getattr(k, "tier", "")) == tier.value]
            active_keys = [k for k in tier_keys if bool(getattr(k, "active", False))]
            
            by_tier[tier.value] = {
                "total_keys": len(tier_keys),
                "active_keys": len(active_keys),
                "inactive_keys": len(tier_keys) - len(active_keys),
                "tier_config": TIER_CONFIG[tier.value],
            }
        
        return {
            "total_keys": len(all_keys),
            "active_keys": sum(1 for k in all_keys if bool(getattr(k, "active", False))),
            "by_tier": by_tier,
        }


# Example usage in admin router:
#
# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from ..auth_db import get_auth_db
# from ..admin_key_manager import AdminKeyManager
# from ..deps import get_api_key
#
# router = APIRouter()
#
# @router.post("/admin/keys")
# def create_api_key(
#     name: str,
#     tier: str = "free",
#     db: Session = Depends(get_auth_db),
#     _: tuple = Depends(get_api_key)  # Protected endpoint
# ):
#     key = AdminKeyManager.create_key(db, name, tier)
#     return {"key": key.key, "name": key.name, "tier": key.tier}
#
# @router.get("/admin/keys")
# def list_api_keys(
#     db: Session = Depends(get_auth_db),
#     _: tuple = Depends(get_api_key)
# ):
#     keys = AdminKeyManager.list_keys(db, active_only=True)
#     return [
#         {
#             "id": k.id,
#             "name": k.name,
#             "tier": k.tier,
#             "owner": k.owner_name,
#             "active": k.active
#         }
#         for k in keys
#     ]
#
# @router.get("/admin/usage")
# def usage_summary(
#     db: Session = Depends(get_auth_db),
#     _: tuple = Depends(get_api_key)
# ):
#     return AdminKeyManager.get_usage_summary(db)
