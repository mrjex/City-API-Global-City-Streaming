from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import aiohttp
from cache.redis_manager import RedisCache
from utils.endpoint_utils import get_city_coordinate, get_configuration

router = APIRouter()
redis_cache = RedisCache()

@router.post("/api/city-coordinates/batch")
async def get_city_coordinates_batch(request: Request):
    """
    Batch endpoint to get coordinates for multiple cities at once.
    """
    try:
        data = await request.json()
        requested_cities = data.get("cities", [])
        country = data.get("country")
        
        if not requested_cities:
            return JSONResponse(
                status_code=400,
                content={"error": "No cities provided in request"}
            )
        
        coordinates = {}
        redis_found = 0
        api_found = 0
        
        for city in requested_cities:
            city_coords = await redis_cache.get_city_coordinates(city)
            if city_coords:
                coordinates[city] = city_coords
                redis_found += 1
            else:
                city_coord = await get_city_coordinate(city)
                if city_coord:
                    print(f"REDIS_LOGS: Retrieved coordinates for '{city}' from external API")
                    coordinates[city] = {
                        "lat": city_coord["latitude"],
                        "lng": city_coord["longitude"]
                    }
                    api_found += 1
                    
                    if country:
                        await redis_cache.update_city_coordinates(city, country, {
                            "lat": city_coord["latitude"],
                            "lng": city_coord["longitude"]
                        })
        
        print(f"REDIS_LOGS: Batch coordinates summary: {redis_found} cities from Redis, {api_found} cities from external API")
        print(f"REDIS_LOGS: Returning coordinates for {len(coordinates)} cities")
        
        return JSONResponse(
            content={"coordinates": coordinates}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process city coordinates request"}
        )

@router.get("/api/static-city-coordinates")
async def get_static_city_coordinates():
    """
    Endpoint to get coordinates for all static cities.
    """
    try:
        config = get_configuration()
        static_cities = config.get("cities", [])
        
        if not static_cities:
            return JSONResponse(
                content={"coordinates": {}}
            )
        
        coordinates = {}
        redis_found = 0
        api_found = 0
        
        for city in static_cities:
            city_coords = await redis_cache.get_city_coordinates(city)
            if city_coords:
                coordinates[city] = city_coords
                redis_found += 1
            else:
                city_coord = await get_city_coordinate(city)
                if city_coord:
                    print(f"REDIS_LOGS: Retrieved coordinates for static city '{city}' from external API")
                    coordinates[city] = {
                        "lat": city_coord["latitude"],
                        "lng": city_coord["longitude"]
                    }
                    api_found += 1
                    
                    country = config.get("defaultCountry", "Unknown")
                    await redis_cache.update_city_coordinates(city, country, {
                        "lat": city_coord["latitude"],
                        "lng": city_coord["longitude"]
                    })
        
        print(f"REDIS_LOGS: Static coordinates summary: {redis_found} cities from Redis, {api_found} cities from external API")
        print(f"REDIS_LOGS: Returning static coordinates for {len(coordinates)} cities")
        
        return JSONResponse(
            content={"coordinates": coordinates}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to process static city coordinates request"}
        )

@router.get("/api/city-coordinates/{city_name}")
async def get_city_coordinates(city_name: str):
    """Get coordinates for a single city"""
    try:
        coordinates = await redis_cache.get_city_coordinates(city_name)
        if coordinates:
            print(f"REDIS_LOGS: Using cached coordinates for {city_name}")
            return coordinates
        
        print(f"REDIS_LOGS: No cached coordinates for {city_name}, fetching from external service")
        coordinates = await get_city_coordinate(city_name)
        
        if coordinates:
            country = "Unknown"
            
            await redis_cache.update_city_coordinates(city_name, country, {
                "lat": coordinates["latitude"],
                "lng": coordinates["longitude"]
            })
            
            return coordinates
        else:
            return JSONResponse(
                status_code=404,
                content={"error": f"Could not find coordinates for {city_name}"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to get coordinates for {city_name}"}
        )

@router.get("/api/city-data/{country}")
async def get_city_data(country: str):
    """Get city data by country"""
    cached_data = await redis_cache.get_city_data(country)
    if cached_data:
        print(f"REDIS_LOGS: Cache hit for country: {country}")
        return cached_data
    
    print(f"REDIS_LOGS: Cache miss for country: {country}. Fetching from external API...")
    
    try:
        async with aiohttp.ClientSession() as session:
            api_url = f"http://api.myweatherapi.com/v2/cities/{country}"
            
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    await redis_cache.set_city_data(country, data)
                    print(f"REDIS_LOGS: Stored city data for {country} in cache")
                    
                    return data
                else:
                    return {"error": "External API error", "status": response.status}
    except Exception as e:
        return {"error": str(e)}

@router.get("/api/video-data/{country}")
async def get_video_data(country: str):
    """Get video data by country"""
    cached_data = await redis_cache.get_video_data(country)
    if cached_data:
        print(f"REDIS_LOGS: Cache hit for video data for country: {country}")
        return cached_data
    
    print(f"REDIS_LOGS: Cache miss for video data for country: {country}. Fetching from external API...")
    
    try:
        async with aiohttp.ClientSession() as session:
            api_url = f"http://api.mycapitalvideos.com/v1/{country}"
            
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    await redis_cache.set_video_data(country, data)
                    print(f"REDIS_LOGS: Stored video data for {country} in cache")
                    
                    return data
                else:
                    return {"error": "External API error", "status": response.status}
    except Exception as e:
        return {"error": str(e)} 