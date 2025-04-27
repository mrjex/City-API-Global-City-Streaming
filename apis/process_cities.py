# TODO - Idea:
#   - Add this as a 'middleware' layer of the "/city-api" container
#   - The purpose of this 'middleware' layer would be to serve as the
#     place where the APIs in "/apis" or the .sh scripts invokes
#     external functionalities. Then, @countryCodeApi.py could also
#     be rewritten/reframed as a middleware layer. An alternative
#     idea is to put this file in "/shared/weather"

import sys
import json

# Add project root to Python path
sys.path.append("/app")
from shared.weather import WeatherAPI

def process_city(city_name):
    try:
        # Initialize WeatherAPI
        try:
            weather_api = WeatherAPI()
        except ValueError as e:
            # print(f"Failed to initialize WeatherAPI: {str(e)}")
            return {
                "city": city_name,
                "temperature": None,
                "error": "Failed to initialize WeatherAPI"
            }

        # print(f"Fetching data for city: {city_name}")
        city_data = weather_api.fetch_city_data(city_name)
        
        if city_data is None:
            return {
                "city": city_name,
                "temperature": None,
                "error": "Failed to fetch weather data"
            }
            
        return {
            "city": city_name,
            "temperature": city_data.get('temperatureCelsius')
        }
    except Exception as e:
        # print(f"Error processing {city_name}: {str(e)}")
        return {
            "city": city_name,
            "temperature": None,
            "error": str(e)
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        city_name = sys.argv[1]
        result = process_city(city_name)
        print(json.dumps(result), flush=True) 