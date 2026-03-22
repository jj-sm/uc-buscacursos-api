"""
Example router demonstrating best practices for the Universal API

This file serves as a template for creating new endpoints with proper
authentication, rate limiting, and documentation.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from ..deps import get_api_key
from ..db import get_db

router = APIRouter()


# ============================================================================
# PYDANTIC MODELS (for request/response validation)
# ============================================================================

class ResourceResponse(BaseModel):
    """Generic response model"""
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True


class ResourceCreate(BaseModel):
    """Model for creating a resource"""
    name: str
    description: Optional[str] = None


class RateLimitInfo(BaseModel):
    """Rate limit information"""
    tier: str
    limit: int
    remaining: int
    reset_in_seconds: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_rate_limit_info(api_key_tuple: tuple) -> RateLimitInfo:
    """Extract rate limit info from the deps return value"""
    api_key, tier, limit_info = api_key_tuple
    return RateLimitInfo(**limit_info)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get(
    "/",
    summary="List endpoints",
    description="Returns a list of available endpoints in this module",
    tags=["Template"]
)
def list_endpoints(
    api_key_tuple: tuple = Depends(get_api_key)
):
    """
    Returns information about available endpoints.
    No database query required - useful for checking you have access.
    """
    api_key, tier, limit_info = api_key_tuple
    
    return {
        "endpoints": [
            "/",
            "/:id",
            "/search",
        ],
        "tier": tier,
        "rate_limit": {
            "limit": limit_info["limit"],
            "remaining": limit_info["remaining"],
            "reset_in_seconds": limit_info["reset_in_seconds"],
        }
    }


@router.get(
    "/{resource_id}",
    summary="Get a resource",
    description="Retrieve a specific resource by ID",
    tags=["Template"],
    responses={
        200: {"description": "Resource found"},
        404: {"description": "Resource not found"},
        403: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
    }
)
def get_resource(
    resource_id: int = Path(..., gt=0, description="Resource ID"),
    db: Session = Depends(get_db),
    api_key_tuple: tuple = Depends(get_api_key)
) -> dict:
    """
    Get a specific resource.
    
    **Path Parameters:**
    - `resource_id` (int, required): The ID of the resource to retrieve
    
    **Authentication:**
    - Requires X-API-Key header
    
    **Rate Limiting:**
    - Depends on your API tier
    - See rate limit headers in response
    
    **Example:**
    ```bash
    curl -H "X-API-Key: your-key" http://localhost:8000/template/123
    ```
    """
    api_key, tier, limit_info = api_key_tuple
    
    # Your code here - example with DB lookup
    # resource = db.query(Resource).filter_by(id=resource_id).first()
    # if not resource:
    #     raise HTTPException(status_code=404, detail="Resource not found")
    
    # For this example, return mock data
    return {
        "id": resource_id,
        "name": f"Resource {resource_id}",
        "description": "Example resource",
        "rate_limit_info": limit_info,
    }


@router.get(
    "/search",
    summary="Search resources",
    description="Search for resources with optional filters",
    tags=["Template"]
)
def search_resources(
    query: Optional[str] = Query(None, min_length=1, description="Search query"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
    api_key_tuple: tuple = Depends(get_api_key)
) -> dict:
    """
    Search for resources with pagination.
    
    **Query Parameters:**
    - `query` (string, optional): Search term
    - `offset` (int, default=0): Pagination offset
    - `limit` (int, default=20, max=100): Results per page
    
    **Example:**
    ```bash
    curl -H "X-API-Key: your-key" \
      "http://localhost:8000/template/search?query=example&limit=10"
    ```
    """
    api_key, tier, limit_info = api_key_tuple
    
    # Your search logic here
    # results = db.query(Resource).filter(...).offset(offset).limit(limit).all()
    
    return {
        "results": [
            {
                "id": 1,
                "name": "Example 1",
                "description": "Test resource",
            }
        ],
        "total": 1,
        "offset": offset,
        "limit": limit,
        "tier": tier,
        "rate_limit": limit_info,
    }


@router.post(
    "/",
    summary="Create a resource",
    description="Create a new resource",
    tags=["Template"],
    status_code=201
)
def create_resource(
    resource: ResourceCreate,
    db: Session = Depends(get_db),
    api_key_tuple: tuple = Depends(get_api_key)
) -> dict:
    """
    Create a new resource.
    
    **Request Body:**
    ```json
    {
      "name": "My Resource",
      "description": "Optional description"
    }
    ```
    
    **Example:**
    ```bash
    curl -X POST \
      -H "X-API-Key: your-key" \
      -H "Content-Type: application/json" \
      -d '{"name": "My Resource"}' \
      http://localhost:8000/template/
    ```
    """
    api_key, tier, limit_info = api_key_tuple
    
    # Check tier for write permissions if needed
    if tier == "free":
        raise HTTPException(
            status_code=403,
            detail="Free tier does not support write operations. Upgrade to Pro."
        )
    
    # Your creation logic here
    # new_resource = Resource(name=resource.name, description=resource.description)
    # db.add(new_resource)
    # db.commit()
    # db.refresh(new_resource)
    
    return {
        "id": 1,
        "name": resource.name,
        "description": resource.description,
        "created": True,
    }


# ============================================================================
# ADVANCED EXAMPLES
# ============================================================================

@router.get(
    "/tier-specific",
    summary="Tier-specific endpoint",
    tags=["Template"]
)
def tier_specific_endpoint(
    api_key_tuple: tuple = Depends(get_api_key)
):
    """
    Example of an endpoint with tier-specific behavior.
    
    Free tier users get limited data, Premium users get everything.
    """
    api_key, tier, limit_info = api_key_tuple
    
    # Define data based on tier
    full_data = {
        "full_analysis": "Detailed analysis here",
        "advanced_metrics": [1, 2, 3, 4, 5],
        "raw_data": "All available data",
    }
    
    free_tier_data = {
        "summary": "Limited analysis",
        "available_tiers": "Pro, Premium, Enterprise",
    }
    
    if tier in ["free"]:
        return free_tier_data
    elif tier in ["pro", "premium"]:
        return {**full_data, "tier": tier}
    else:  # enterprise
        return {**full_data, "tier": tier, "priority": "high"}


# ============================================================================
# ERROR HANDLING EXAMPLES
# ============================================================================

@router.get(
    "/error-examples",
    summary="Error handling examples",
    tags=["Template"]
)
def error_examples(
    error_type: Optional[str] = Query(None, description="Type of error to demo"),
    api_key_tuple: tuple = Depends(get_api_key)
):
    """
    Demonstration of various error responses.
    
    **Query Parameters:**
    - `error_type` (string): "not_found", "invalid", "server_error"
    """
    
    if error_type == "not_found":
        raise HTTPException(
            status_code=404,
            detail="Resource not found"
        )
    
    if error_type == "invalid":
        raise HTTPException(
            status_code=400,
            detail="Invalid request parameters"
        )
    
    if error_type == "server_error":
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
    
    return {
        "status": "ok",
        "examples_available": ["not_found", "invalid", "server_error"]
    }
