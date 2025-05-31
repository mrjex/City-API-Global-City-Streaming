from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from utils.endpoint_utils import execute_country_cities_script
from cache.redis_manager import RedisCache

router = APIRouter()
redis_cache = RedisCache()

@router.post("/api/selected-country")
async def receive_selected_country(request: Request):
    try:
        data = await request.json()
        country = data.get('country')

        cached_city_data = await redis_cache.get_city_data(country)
        cached_video_data = await redis_cache.get_video_data(country)

        if cached_city_data and cached_video_data:
            return JSONResponse(content={
                "success": True,
                "country": country,
                "country_code": cached_city_data.get('country_code'),
                "cities": cached_city_data.get('cities', []),
                "capital_city_video_link": cached_video_data.get('video_url'),
                "capital_city_description": cached_video_data.get('description')
            })

        script_result = await execute_country_cities_script(country)
        
        if script_result.get('success'):
            cities = script_result.get('cities', [])
            capital_city = cities[0].get('city') if cities else None
            country_code = script_result.get('country_code', '')
            
            await redis_cache.set_city_data(country, {
                'country': country,
                'country_code': country_code,
                'cities': cities
            })
            
            if capital_city:
                await redis_cache.set_video_data(country, {
                    'country': country,
                    'capital_city': capital_city,
                    'video_url': script_result.get('capital_city_video_link'),
                    'description': script_result.get('capital_city_description')
                })
            
            for city_data in cities:
                city_name = city_data.get('city')
                if city_name and 'latitude' in city_data and 'longitude' in city_data:
                    print(f"REDIS_LOGS: Storing coordinates for dynamic city {city_name} in country {country}")
                    await redis_cache.update_city_coordinates(city_name, country, {
                        "lat": float(city_data.get('latitude')),
                        "lng": float(city_data.get('longitude'))
                    })
            
            return JSONResponse(content=script_result)
        else:
            return JSONResponse(
                content={"error": "Failed to fetch country data"},
                status_code=500
            )
            
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        ) 