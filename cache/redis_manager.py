from redis import Redis, RedisError
import yaml
import json
from typing import Dict, Optional, Any, List
import os
from pathlib import Path

class CityOverrides:
    def __init__(self):
        self.overrides = self._load_overrides()
        self._watch_overrides_file()
    
    def _load_overrides(self) -> Dict[str, Any]:
        try:
            with open('/app/city-api/config/city-edits.yml', 'r') as f:
                data = yaml.safe_load(f)
                print("REDIS_LOGS: Loaded city overrides:", data.get('countries', {}))
                return data.get('countries', {})
        except Exception as e:
            print(f"REDIS_LOGS: Error loading city overrides: {str(e)}")
            return {}
    
    def _watch_overrides_file(self):
        """Set up a file watcher for city-edits.yml"""
        import threading
        def watch_file():
            last_mtime = Path('/app/city-api/config/city-edits.yml').stat().st_mtime
            while True:
                try:
                    current_mtime = Path('/app/city-api/config/city-edits.yml').stat().st_mtime
                    if current_mtime != last_mtime:
                        print("REDIS_LOGS: Detected changes in city-edits.yml, reloading...")
                        self.overrides = self._load_overrides()
                        last_mtime = current_mtime
                    import time
                    time.sleep(1)
                except Exception as e:
                    print(f"REDIS_LOGS: Error watching overrides file: {str(e)}")
                    
        thread = threading.Thread(target=watch_file, daemon=True)
        thread.start()
    
    def get_override(self, country: str, city: str) -> Optional[Dict[str, Any]]:
        key = f"{country}, {city}"
        override = self.overrides.get(key, {})
        if override:
            print(f"REDIS_LOGS: Found override for {key}: {override}")
        return override

class RedisCache:
    # TTL constants
    CITY_DATA_TTL = 604800  # 1 week
    VIDEO_DATA_TTL = 604800  # 1 week
    
    # Key prefixes for the new structure
    DYNAMIC_COUNTRIES_ALL_KEY = "dynamic:countries:all"
    DYNAMIC_COUNTRY_PREFIX = "dynamic:country:"
    DYNAMIC_CITY_PREFIX = "dynamic:city:"
    STATIC_CITY_PREFIX = "static:city:"
    STATIC_CITIES_ALL_KEY = "static:cities:all"
    
    def __init__(self):
        self.redis_client = Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            decode_responses=True
        )
        self.overrides = CityOverrides()
        
    async def get_city_data(self, country: str) -> Optional[Dict[str, Any]]:
        """Get cached city data with TTL check"""
        try:
            # Only use the new structure
            if self.redis_client.hexists("dynamic:country_codes", country):
                print(f"REDIS_LOGS: Found country {country} in new structure")
                
                # Get country data
                country_key = f"{self.DYNAMIC_COUNTRY_PREFIX}{country}"
                if self.redis_client.exists(country_key):
                    country_data = self.redis_client.hgetall(country_key)
                    
                    # Get city list
                    city_list_str = country_data.get("cities", "[]")
                    try:
                        city_list = json.loads(city_list_str)
                    except:
                        city_list = []
                    
                    # Build response
                    cities = []
                    for city_name in city_list:
                        city_key = f"{self.DYNAMIC_CITY_PREFIX}{country}:{city_name}"
                        if self.redis_client.exists(city_key):
                            city_data = self.redis_client.hgetall(city_key)
                            cities.append({
                                "city": city_name,
                                **{k: v for k, v in city_data.items() if k != "city"}
                            })
                    
                    return {
                        "country": country,
                        "country_code": country_data.get("country_code", ""),
                        "cities": cities
                    }
            
            # Fall back to old structure if new structure doesn't have this country
            # COMMENTED OUT - no longer using old structure
            # cache_key = f"city_data:{country}"
            # data = self.redis_client.get(cache_key)
            # if data:
            #     print(f"Cache hit for {cache_key} (old structure)")
            #     return json.loads(data)
            print(f"REDIS_LOGS: Cache miss for country: {country}")
            return None
        except Exception as e:
            print(f"REDIS_LOGS: Error getting city data from cache: {str(e)}")
            return None

    async def set_city_data(self, country: str, data: Dict[str, Any]) -> bool:
        """Set city data with overrides"""
        try:
            # Apply overrides for each city
            cities = data.get('cities', [])
            country_code = data.get('country_code', '')
            
            for city in cities:
                city_name = city.get('city')
                if city_name:
                    override = self.overrides.get_override(country, city_name)
                    if override:
                        print(f"REDIS_LOGS: Applying override for {country}, {city_name}")
                        if 'description' in override:
                            city['description'] = override['description']
            
            # Store using only the new structure 
            # COMMENTED OUT - no longer using old structure
            # # 1. Old structure
            # cache_key = f"city_data:{country}"
            # self.redis_client.setex(
            #     cache_key,
            #     self.CITY_DATA_TTL,  # 1 week
            #     json.dumps(data)
            # )
            
            # 2. New structure
            # Add to dynamic countries set
            self.redis_client.sadd(self.DYNAMIC_COUNTRIES_ALL_KEY, country)
            
            # Store country code
            self.redis_client.hset("dynamic:country_codes", country, country_code)
            
            # Create/update country entry
            country_key = f"{self.DYNAMIC_COUNTRY_PREFIX}{country}"
            city_names = [city.get('city') for city in cities if city.get('city')]
            
            pipe = self.redis_client.pipeline()
            pipe.hset(country_key, "country_code", country_code)
            pipe.hset(country_key, "cities", json.dumps(city_names))
            
            # Set expiration on country key
            pipe.expire(country_key, self.CITY_DATA_TTL)
            
            # Store each city
            for city in cities:
                city_name = city.get('city')
                if city_name:
                    city_key = f"{self.DYNAMIC_CITY_PREFIX}{country}:{city_name}"
                    
                    # Delete old data if it exists
                    pipe.delete(city_key)
                    
                    # Add all city fields
                    for field, value in city.items():
                        if field != 'city':  # Skip city name as it's in the key
                            pipe.hset(city_key, field, str(value))
                    
                    # Set expiration
                    pipe.expire(city_key, self.CITY_DATA_TTL)
            
            # Execute all commands
            pipe.execute()
            
            print(f"REDIS_LOGS: Set cache for {country} using new structure")
            return True
        except Exception as e:
            print(f"REDIS_LOGS: Error setting city data in cache: {str(e)}")
            return False

    async def get_video_data(self, country: str) -> Optional[Dict[str, Any]]:
        """Get cached video data"""
        try:
            # Only use new structure
            capital_key = None
            
            # Get country data to find capital city
            country_key = f"{self.DYNAMIC_COUNTRY_PREFIX}{country}"
            if self.redis_client.exists(country_key):
                country_data = self.redis_client.hgetall(country_key)
                
                # Try to find capital city
                city_list_str = country_data.get("cities", "[]")
                try:
                    city_list = json.loads(city_list_str)
                    if city_list:
                        # Assume first city is capital (or we could store this explicitly)
                        capital_city = city_list[0]
                        capital_key = f"{self.DYNAMIC_CITY_PREFIX}{country}:{capital_city}"
                except:
                    pass
            
            # If we found a capital city, get its data
            if capital_key and self.redis_client.exists(capital_key):
                city_data = self.redis_client.hgetall(capital_key)
                if "video_url" in city_data or "description" in city_data:
                    print(f"REDIS_LOGS: Found video data for {country} in new structure")
                    return {
                        "country": country,
                        "capital_city": city_data.get("city", ""),
                        "video_url": city_data.get("video_url", ""),
                        "description": city_data.get("description", "")
                    }
            
            # Fall back to old structure - COMMENTED OUT
            # cache_key = f"capital_video:{country}"
            # data = self.redis_client.get(cache_key)
            # if data:
            #     print(f"Cache hit for {cache_key} (old structure)")
            #     return json.loads(data)
            print(f"REDIS_LOGS: Cache miss for video data: {country}")
            return None
        except Exception as e:
            print(f"REDIS_LOGS: Error getting video data from cache: {str(e)}")
            return None

    async def set_video_data(self, country: str, data: Dict[str, Any]) -> bool:
        """Set video data with overrides"""
        try:
            capital_city = data.get('capital_city')
            if capital_city:
                override = self.overrides.get_override(country, capital_city)
                if override:
                    print(f"REDIS_LOGS: Applying video override for {country}, {capital_city}")
                    if override.get('video'):
                        data['video_url'] = override['video']
                    if override.get('description'):
                        data['description'] = override['description']
            
            # Store using only new structure
            
            # COMMENTED OUT - no longer using old structure
            # # 1. Old structure
            # cache_key = f"capital_video:{country}"
            # self.redis_client.setex(
            #     cache_key,
            #     self.VIDEO_DATA_TTL,  # 1 week
            #     json.dumps(data)
            # )
            
            # 2. New structure - update city data with video info
            if capital_city:
                city_key = f"{self.DYNAMIC_CITY_PREFIX}{country}:{capital_city}"
                
                pipe = self.redis_client.pipeline()
                
                if data.get('video_url'):
                    pipe.hset(city_key, "video_url", data['video_url'])
                
                if data.get('description'):
                    pipe.hset(city_key, "description", data['description'])
                
                # Refresh TTL
                pipe.expire(city_key, self.VIDEO_DATA_TTL)
                pipe.execute()
            
            print(f"REDIS_LOGS: Set video data for {country} using new structure")
            return True
        except Exception as e:
            print(f"REDIS_LOGS: Error setting video data in cache: {str(e)}")
            return False

    def clear_cache(self, country: str = None):
        """Clear cache for a country or all cache if country is None"""
        try:
            if country:
                # Clear old structure - COMMENTED OUT
                # keys = [
                #     f"city_data:{country}",
                #     f"capital_video:{country}"
                # ]
                # for key in keys:
                #     self.redis_client.delete(key)
                
                # Clear new structure
                country_key = f"{self.DYNAMIC_COUNTRY_PREFIX}{country}"
                
                # Get city list to delete all city keys
                if self.redis_client.exists(country_key):
                    country_data = self.redis_client.hgetall(country_key)
                    city_list_str = country_data.get("cities", "[]")
                    try:
                        city_list = json.loads(city_list_str)
                        for city_name in city_list:
                            city_key = f"{self.DYNAMIC_CITY_PREFIX}{country}:{city_name}"
                            self.redis_client.delete(city_key)
                    except:
                        pass
                
                # Delete country key and remove from set
                self.redis_client.delete(country_key)
                self.redis_client.srem(self.DYNAMIC_COUNTRIES_ALL_KEY, country)
                self.redis_client.hdel("dynamic:country_codes", country)
                
                print(f"REDIS_LOGS: Cleared cache for {country} using new structure")
            else:
                # Clear everything
                self.redis_client.flushall()
                print("REDIS_LOGS: Cleared all cache")
        except Exception as e:
            print(f"REDIS_LOGS: Error clearing cache: {str(e)}")
    
    async def get_city_coordinates(self, city_name: str) -> Optional[Dict[str, float]]:
        """Get city coordinates from Redis"""
        try:
            # First check static cities
            static_city_key = f"{self.STATIC_CITY_PREFIX}{city_name}"
            if self.redis_client.exists(static_city_key):
                city_data = self.redis_client.hgetall(static_city_key)
                if "latitude" in city_data and "longitude" in city_data:
                    print(f"REDIS_LOGS: DEBUG: Found coordinates for '{city_name}' in STATIC city data in Redis")
                    return {
                        "lat": float(city_data["latitude"]),
                        "lng": float(city_data["longitude"])
                    }
            
            # Then check all dynamic countries for this city
            dynamic_countries = self.redis_client.smembers(self.DYNAMIC_COUNTRIES_ALL_KEY)
            for country in dynamic_countries:
                country_key = f"{self.DYNAMIC_COUNTRY_PREFIX}{country}"
                if self.redis_client.exists(country_key):
                    country_data = self.redis_client.hgetall(country_key)
                    city_list_str = country_data.get("cities", "[]")
                    try:
                        city_list = json.loads(city_list_str)
                        if city_name in city_list:
                            city_key = f"{self.DYNAMIC_CITY_PREFIX}{country}:{city_name}"
                            city_data = self.redis_client.hgetall(city_key)
                            if "latitude" in city_data and "longitude" in city_data:
                                print(f"REDIS_LOGS: DEBUG: Found coordinates for '{city_name}' in DYNAMIC city data in Redis (country: {country})")
                                return {
                                    "lat": float(city_data["latitude"]),
                                    "lng": float(city_data["longitude"])
                                }
                    except:
                        continue
            
            # Not found in Redis
            print(f"REDIS_LOGS: DEBUG: Could not find coordinates for '{city_name}' in Redis")
            return None
        except Exception as e:
            print(f"REDIS_LOGS: Error getting city coordinates from Redis: {str(e)}")
            return None
            
    async def update_city_coordinates(self, city_name: str, country: str, coordinates: Dict[str, float]) -> bool:
        """Update coordinates for a dynamic city in Redis"""
        try:
            if not city_name or not country:
                print(f"REDIS_LOGS: Cannot update coordinates - missing city name or country")
                return False
                
            print(f"REDIS_LOGS: Attempting to update coordinates for '{city_name}' in country '{country}'")
            
            # First check if this is a dynamic city that exists
            city_key = f"{self.DYNAMIC_CITY_PREFIX}{country}:{city_name}"
            
            # Check if the city belongs to this country
            country_key = f"{self.DYNAMIC_COUNTRY_PREFIX}{country}"
            
            # Use a pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            if not self.redis_client.exists(country_key):
                # Country doesn't exist in Redis yet, add it
                print(f"REDIS_LOGS: Adding new country {country} to Redis")
                pipe.sadd(self.DYNAMIC_COUNTRIES_ALL_KEY, country)
                pipe.hset(country_key, "cities", json.dumps([city_name]))
                pipe.expire(country_key, self.CITY_DATA_TTL)
            else:
                # Country exists, check if city is in the list
                country_data = self.redis_client.hgetall(country_key)
                city_list_str = country_data.get("cities", "[]")
                try:
                    city_list = json.loads(city_list_str)
                    if city_name not in city_list:
                        # Add the city to the country's city list
                        city_list.append(city_name)
                        pipe.hset(country_key, "cities", json.dumps(city_list))
                except json.JSONDecodeError:
                    # Invalid JSON, create a new list
                    pipe.hset(country_key, "cities", json.dumps([city_name]))
            
            # Update the city coordinates
            pipe.hset(city_key, "latitude", str(coordinates["lat"]))
            pipe.hset(city_key, "longitude", str(coordinates["lng"]))
            
            # Make sure we keep any existing data like temperature
            existing_data = self.redis_client.hgetall(city_key)
            if "temperature" in existing_data:
                # Keep the existing temperature
                pipe.hset(city_key, "temperature", existing_data["temperature"])
            
            # Extend TTL for the city key
            pipe.expire(city_key, self.CITY_DATA_TTL)
            
            # Execute all commands as a transaction
            result = pipe.execute()
            
            print(f"REDIS_LOGS: Successfully stored coordinates for '{city_name}' in Redis (lat={coordinates['lat']}, lng={coordinates['lng']})")
            print(f"REDIS_LOGS: Redis key: {city_key}")
            
            # Debugging - print what's now in Redis for this city
            updated_data = self.redis_client.hgetall(city_key)
            print(f"REDIS_LOGS: Updated city data in Redis: {updated_data}")
            
            return True
        except Exception as e:
            print(f"REDIS_LOGS: Error updating city coordinates in Redis: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def print_redis_structure(self):
        """Print the current Redis structure for debugging"""
        try:
            structure = {
                "static": {},
                "dynamic": {}
            }
            
            # Get static cities
            static_cities = self.redis_client.smembers("static:cities:all")
            if static_cities:
                structure["static"]["cities"] = list(static_cities)
                # Get a sample city
                if len(static_cities) > 0:
                    sample_city = next(iter(static_cities))
                    structure["static"]["sample_city"] = {
                        "key": f"static:city:{sample_city}",
                        "data": self.redis_client.hgetall(f"static:city:{sample_city}")
                    }
            
            # Get dynamic countries
            dynamic_countries = self.redis_client.smembers("dynamic:countries:all")
            if dynamic_countries:
                structure["dynamic"]["countries"] = list(dynamic_countries)
                # Get a sample country
                if len(dynamic_countries) > 0:
                    sample_country = next(iter(dynamic_countries))
                    country_key = f"dynamic:country:{sample_country}"
                    country_data = self.redis_client.hgetall(country_key)
                    structure["dynamic"]["sample_country"] = {
                        "key": country_key,
                        "data": country_data
                    }
                    
                    # Get cities for this country
                    city_list_str = country_data.get("cities", "[]")
                    try:
                        city_list = json.loads(city_list_str)
                        if city_list and len(city_list) > 0:
                            sample_city = city_list[0]
                            city_key = f"dynamic:city:{sample_country}:{sample_city}"
                            structure["dynamic"]["sample_city"] = {
                                "key": city_key,
                                "data": self.redis_client.hgetall(city_key)
                            }
                    except:
                        pass
            
            # Also include the legacy structure (COMMENTED OUT)
            # structure["legacy"] = {
            #     "city_data": {},
            #     "capital_video": {}
            # }
            
            # Get sample legacy keys
            # for key in self.redis_client.keys("city_data:*")[:1]:
            #     structure["legacy"]["city_data"][key] = "JSON string (truncated)"
            
            # for key in self.redis_client.keys("capital_video:*")[:1]:
            #     structure["legacy"]["capital_video"][key] = "JSON string (truncated)"
            
            print("REDIS_LOGS: Current Redis Structure:")
            print(json.dumps(structure, indent=2))
            
            return structure
        except Exception as e:
            print(f"REDIS_LOGS: Error printing Redis structure: {str(e)}")
            return {} 