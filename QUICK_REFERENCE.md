# Universal API - Quick Reference Card

## 🔐 Authentication & Rate Limiting

### API Tiers
```
FREE:        10 req/s   (max burst: 20)       ← Development
PRO:        100 req/s   (max burst: 200)      ← Small production
PREMIUM:  1,000 req/s   (max burst: 2,000)    ← Enterprise
ENTERPRISE: Unlimited   (custom SLA)          ← Critical systems
```

### Using API Key
```bash
# Header-based authentication
curl -H "X-API-Key: your-key" http://localhost:8000/airports/info/airport/KJFK
```

### Rate Limit Response
```json
{
  "detail": "Rate limit exceeded. Tier: Free allows 10 req/s"
}
```

---

## 📝 Creating an Endpoint

### Basic Endpoint
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..deps import get_api_key
from ..db import get_db

router = APIRouter()

@router.get("/data")
def get_data(
    db: Session = Depends(get_db),
    api_key_tuple: tuple = Depends(get_api_key)
):
    api_key, tier, limit_info = api_key_tuple
    
    return {
        "data": "value",
        "tier": tier,
        "remaining": limit_info["remaining"]
    }
```

### Tier-Specific Logic
```python
if tier == "free":
    raise HTTPException(403, "Upgrade to Pro for this feature")

if tier in ["pro", "premium"]:
    # Give more data
    pass
```

### With Database
```python
@router.get("/airports/{icao}")
def get_airport(
    icao: str,
    db: Session = Depends(get_db),
    api_key_tuple: tuple = Depends(get_api_key)
):
    api_key, tier, limit_info = api_key_tuple
    airport = db.query(Airport).filter_by(code=icao).first()
    
    if not airport:
        raise HTTPException(404, "Not found")
    
    return airport
```

---

## 🔑 Creating API Keys (Python)

```python
from app.auth_db import SessionLocal
from app.auth_models import APIKey, TierEnum
from app.admin_key_manager import AdminKeyManager
import secrets

db = SessionLocal()

# Method 1: Direct
key = APIKey(
    key=secrets.token_urlsafe(32),
    name="My App",
    tier=TierEnum.PRO.value,
    owner_name="John Doe"
)
db.add(key)
db.commit()

# Method 2: Using AdminKeyManager
key = AdminKeyManager.create_key(
    db, 
    name="My App",
    tier="pro",
    owner_name="John Doe"
)

print(f"API Key: {key.key}")
```

---

## 📊 API Response Structure

### Success Response
```json
{
  "data": {...},
  "tier": "pro",
  "rate_limit": {
    "limit": 100,
    "remaining": 87,
    "reset_in_seconds": 1
  }
}
```

### Error Responses
```json
// 403 Unauthorized
{"detail": "Invalid or inactive API Key"}

// 429 Rate Limited
{"detail": "Rate limit exceeded. Tier: Free allows 10 req/s"}

// 404 Not Found
{"detail": "Resource not found"}

// 422 Validation Error
{"detail": "Invalid request data"}
```

---

## 🛠️ Environment Setup

```bash
# Clone and setup
cp .env.example .env
python -c "from app.auth_models import Base; from app.auth_db import engine; Base.metadata.create_all(engine)"

# Run development
DEBUG=1 uvicorn app.main:app --reload

# Run production
python run.py
```

---

## 📍 Endpoints

### System
- `GET  /` - API info
- `GET  /health` - Health check

### Template (Examples)
- `GET  /template/` - List endpoints
- `GET  /template/{id}` - Get resource
- `GET  /template/search` - Search
- `POST /template/` - Create (tier-restricted)

### Admin (Protected)
- `GET  /admin/keys` - List API keys
- `POST /admin/keys` - Create key
- `GET  /admin/usage` - Usage stats

### Data Endpoints
- `GET  /airports/...`
- `GET  /airspace/...`
- `GET  /enroute/...`
- `GET  /sectorfile/...`
- etc.

---

## 🧪 Testing

### Test Free Tier
```bash
export KEY="your-free-key"
for i in {1..15}; do
  curl -H "X-API-Key: $KEY" http://localhost:8000/airports/info/airport/KJFK
done
# Should fail on request 11
```

### Test Tier Info
```bash
curl http://localhost:8000/
```

### Test Template Endpoints
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/template/
curl -H "X-API-Key: your-key" http://localhost:8000/template/123
curl -H "X-API-Key: your-key" http://localhost:8000/template/search?query=test
```

---

## 📚 Files Reference

| File | Purpose |
|------|---------|
| `auth_models.py` | API key models & tier config |
| `deps.py` | Rate limiting & authentication |
| `generic_models.py` | Template data models |
| `rate_limiter.py` | Tier configuration utilities |
| `admin_key_manager.py` | API key management |
| `routers/template.py` | Example endpoints |
| `API_TEMPLATE_GUIDE.md` | Full documentation |
| `REFACTORING_SUMMARY.md` | Migration guide |

---

## 🔄 Tier Configuration

Edit `TIER_CONFIG` in `auth_models.py`:

```python
TIER_CONFIG = {
    "free": {
        "requests_per_second": 10,      # ← Change here
        "max_burst": 20,
        "description": "Free tier...",
    },
    "pro": {
        "requests_per_second": 100,     # ← Or here
        "max_burst": 200,
        ...
    },
    ...
}
```

---

## 💡 Tips & Tricks

### Get Rate Limit Info in Your Code
```python
api_key, tier, limit_info = api_key_tuple
remaining = limit_info["remaining"]
if remaining < 5:
    logger.warning(f"Low rate limit: {remaining} requests left")
```

### Restrict by Tier
```python
TIER_REQUIRED = {
    "premium_feature": ["pro", "premium", "enterprise"],
    "write_operations": ["pro", "premium", "enterprise"],
}

if tier not in TIER_REQUIRED["write_operations"]:
    raise HTTPException(403, "Upgrade required")
```

### Debug Mode (Disable Auth)
```bash
DEBUG=1 uvicorn app.main:app --reload
```

---

## ❓ Common Issues

**Issue:** Rate limit error on first request  
**Solution:** Check that your tier is correctly assigned in database

**Issue:** API key not found  
**Solution:** Verify key exists in auth database:
```python
from app.admin_key_manager import AdminKeyManager
keys = AdminKeyManager.list_keys(db)
print([k.key for k in keys])
```

**Issue:** Can't import modules  
**Solution:** Make sure you're in venv: `source venv/bin/activate`

---

**Last Updated:** March 21, 2026  
**Version:** 1.0.0
