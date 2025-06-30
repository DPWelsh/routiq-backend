# Backend API Integration Guide

## Overview
This guide documents best practices for adding new API endpoints to the Routiq Backend, based on lessons learned during the reengagement API implementation.

## Router Pattern Standards

### ✅ Correct Router Pattern

```python
# src/api/your_module.py
from fastapi import APIRouter

# Create router WITHOUT prefix - let main.py handle it
router = APIRouter()

@router.get("/test")
def test_endpoint():
    return {"message": "Working!"}

@router.get("/{organization_id}/data")
def get_data(organization_id: str):
    return {"organization_id": organization_id}
```

```python
# src/api/main.py
try:
    from src.api.your_module import router as your_router
    app.include_router(your_router, prefix="/api/v1/your-module", tags=["Your Module"])
    logger.info("✅ Your module endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Your module endpoints not available: {e}")
```

### ❌ Incorrect Router Pattern (Common Mistake)

```python
# DON'T DO THIS - causes endpoints to not appear in docs
router = APIRouter(prefix="/api/v1/your-module", tags=["Your Module"])

# And then in main.py:
app.include_router(your_router)  # Missing prefix/tags
```

## Common Integration Issues

### Issue 1: Router Prefix Conflicts
**Problem**: Defining prefix in both router constructor AND main.py inclusion
**Solution**: Only define prefix in main.py `include_router()` call

### Issue 2: Import Path Inconsistencies
**Problem**: Using wrong import patterns
**Solution**: Follow existing patterns:
```python
# ✅ Correct
from src.database import db
from src.api.auth import verify_organization_access

# ❌ Wrong
from database import db
from api.auth import verify_organization_access
```

### Issue 3: Database Pattern Mismatches
**Problem**: Mixing async/sync database patterns
**Solution**: Use existing synchronous pattern:
```python
# ✅ Correct - matches existing codebase
try:
    with db.get_cursor() as cursor:
        cursor.execute(query, [param1, param2])
        result = cursor.fetchone()
    return result
except Exception as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Database error")

# ❌ Wrong - async pattern not used in this codebase
result = await db.fetch_one(query, param1, param2)
```

### Issue 4: Parameter Placeholder Issues
**Problem**: Using PostgreSQL-style `$1, $2` parameters
**Solution**: Use `%s, %s` format:
```python
# ✅ Correct
cursor.execute("SELECT * FROM table WHERE id = %s AND org = %s", [id_val, org_val])

# ❌ Wrong
cursor.execute("SELECT * FROM table WHERE id = $1 AND org = $2", [id_val, org_val])
```

## Step-by-Step Integration Process

### 1. Create Your Router File
```python
# src/api/your_feature.py
"""
Your Feature API - Brief description
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from src.database import db
from src.api.auth import verify_organization_access

logger = logging.getLogger(__name__)

# Create router (prefix added in main.py)
router = APIRouter()

@router.get("/test")
def test_your_feature():
    """Test endpoint to verify router is working"""
    return {
        "message": "Your feature router is working!",
        "timestamp": datetime.now().isoformat(),
        "status": "success"
    }

@router.get("/{organization_id}/data")
def get_your_data(
    organization_id: str,
    verified_org_id: str = Depends(verify_organization_access)
):
    """Your main endpoint with organization verification"""
    try:
        with db.get_cursor() as cursor:
            query = "SELECT * FROM your_table WHERE organization_id = %s"
            cursor.execute(query, [organization_id])
            result = cursor.fetchone()
            
        return {
            "organization_id": organization_id,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in your_feature for {organization_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch data")
```

### 2. Add Router to Main.py
Add your router import and inclusion in the appropriate section:

```python
# src/api/main.py
# Add this in the router inclusion section:

# Try to include Your Feature endpoints
try:
    from src.api.your_feature import router as your_feature_router
    app.include_router(your_feature_router, prefix="/api/v1/your-feature", tags=["Your Feature"])
    logger.info("✅ Your Feature endpoints enabled")
except Exception as e:
    logger.warning(f"⚠️ Your Feature endpoints not available: {e}")
```

### 3. Test Locally
```bash
# Start local development server
python src/api/start.py

# Test your endpoints
curl "http://localhost:8000/api/v1/your-feature/test"
curl "http://localhost:8000/api/v1/your-feature/test-org/data"

# Check docs
open "http://localhost:8000/docs"
```

### 4. Deploy and Verify
```bash
# Commit and push
git add src/api/your_feature.py src/api/main.py
git commit -m "Add your feature API endpoints"
git push

# Wait 60 seconds for Railway deployment
sleep 60

# Test production endpoints
curl "https://routiq-backend-prod.up.railway.app/api/v1/your-feature/test"

# Verify in production docs
open "https://routiq-backend-prod.up.railway.app/docs"
```

## Testing Checklist

Before deploying new API endpoints:

- [ ] Router created without prefix in constructor
- [ ] Router included in main.py with proper prefix and tags
- [ ] Test endpoint responds locally
- [ ] Main endpoints work with test data locally
- [ ] All imports follow existing patterns
- [ ] Database queries use synchronous pattern with proper error handling
- [ ] Authentication dependencies added where needed
- [ ] Logging added for debugging
- [ ] Endpoints appear in local `/docs`
- [ ] Production deployment successful
- [ ] Endpoints appear in production `/docs`
- [ ] Test endpoints respond in production

## Troubleshooting

### Endpoints Not Appearing in Docs
1. Check router prefix pattern (most common issue)
2. Verify import path in main.py
3. Check for Python syntax errors
4. Look at Railway deployment logs

### Import Errors
1. Ensure all imports follow `from src.module import item` pattern
2. Check that referenced modules exist
3. Verify no circular imports

### Database Errors
1. Use synchronous `db.get_cursor()` pattern
2. Use `%s` parameter placeholders, not `$1`
3. Always wrap in try/catch with proper error handling
4. Check database connection and table existence

### Authentication Issues
1. Add `verify_organization_access` dependency to protected endpoints
2. Ensure organization_id parameter matches verified_org_id
3. Test with valid authentication tokens

## Architecture Philosophy

**Lean PostgreSQL-First Approach:**
- Use SQL views for complex business logic
- Keep API endpoints as thin controllers
- Minimize Python business logic in favor of database views
- Focus on JSON serialization rather than complex calculations

**Example:**
```python
# ✅ Preferred - thin controller querying SQL view
def get_analytics(organization_id: str):
    with db.get_cursor() as cursor:
        cursor.execute("SELECT * FROM analytics_view WHERE org_id = %s", [organization_id])
        return cursor.fetchone()

# ❌ Avoid - complex business logic in Python
def get_analytics(organization_id: str):
    # 50 lines of complex calculations...
    # Multiple database queries...
    # Complex aggregations...
```

## Case Study: Reengagement API Success

**Problem**: Router defined prefix in constructor, causing endpoints to not appear in docs
**Root Cause**: Double prefix definition (router + main.py)
**Solution**: Remove prefix from router constructor, add in main.py inclusion
**Result**: All endpoints working in production within minutes

**Key Takeaway**: Follow established patterns exactly - the codebase has consistent patterns that work reliably when followed.

---

*This guide should be updated as new patterns emerge and lessons are learned.* 