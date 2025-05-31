from fastapi import APIRouter, Request
from cache.redis_manager import RedisCache

router = APIRouter()
redis_cache = RedisCache()

@router.post("/api/cache/clear")
async def clear_cache(request: Request):
    """Clear Redis cache"""
    try:
        data = await request.json()
        country = data.get('country')
        
        redis_cache.clear_cache(country)
        
        print(f"REDIS_LOGS: Cache cleared for country: {country if country else 'ALL'}")
        return {"status": "success", "message": f"Cache cleared for {country if country else 'ALL'}"}
    except Exception as e:
        return {"status": "error", "message": str(e)} 