# The utils for 'main.py' file, only containing non-endpoint functions of FastAPI which
# are helper functions called by the endpoints.

import os
import json
import docker
import yaml
from pathlib import Path
import subprocess
import asyncio
import aiohttp
from kafka import KafkaProducer, KafkaConsumer

# Kafka configuration
KAFKA_NODES = "kafka:9092"
CONTROL_TOPIC = "city-control"

# Initialize Docker client with improved error handling
def get_docker_client():
    try:
        # Try with default socket path
        client = docker.from_env()
        # Test connection
        client.ping()
        return client
    except Exception as e:
        # print(f"Failed to connect to Docker daemon using default socket: {str(e)}")
        pass
        
    # Try with explicit socket path
    try:
        socket_paths = [
            '/var/run/docker.sock',           # Standard Linux path
            '/run/docker.sock',               # Alternative Linux path
            '//./pipe/docker_engine',         # Windows path
            os.environ.get('DOCKER_HOST', '') # From environment variable
        ]
        
        for socket_path in socket_paths:
            if not socket_path:
                continue
                
            try:
                if socket_path.startswith('//./pipe'):
                    # Windows named pipe
                    client = docker.DockerClient(base_url=socket_path)
                else:
                    # Unix socket
                    client = docker.DockerClient(base_url=f"unix://{socket_path}")
                
                # Test connection
                client.ping()
                # print(f"Successfully connected to Docker daemon using {socket_path}")
                return client
            except Exception as socket_error:
                # print(f"Failed to connect using {socket_path}: {str(socket_error)}")
                continue
                
        # print("All attempts to connect to Docker daemon failed")
        return None
    except Exception as e:
        # print(f"Error setting up Docker client: {str(e)}")
        return None

# Initialize Kafka producer for control messages
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_NODES,
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )

# Initialize Kafka consumer for control messages
def get_kafka_consumer():
    return KafkaConsumer(
        CONTROL_TOPIC,
        bootstrap_servers=KAFKA_NODES,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

# Function to start control message consumer in a background thread
def start_control_consumer(dynamic_cities):
    def consume_messages():
        consumer = get_kafka_consumer()
        # print("[DEBUG] Started control message consumer")
        try:
            for message in consumer:
                try:
                    control_data = message.value
                    if control_data.get('action') == 'UPDATE_CITIES':
                        nonlocal dynamic_cities
                        new_cities = control_data.get('data', {}).get('cities', [])
                        dynamic_cities = new_cities
                        # print(f"[DEBUG] Updated dynamic cities list: {dynamic_cities}")
                except Exception as e:
                    # print(f"[ERROR] Error processing control message: {str(e)}")
                    pass
        except Exception as e:
            # print(f"[ERROR] Control consumer error: {str(e)}")
            pass

    import threading
    consumer_thread = threading.Thread(target=consume_messages, daemon=True)
    consumer_thread.start()

# Function to update dynamic cities in configuration
def update_dynamic_cities(cities, is_first_batch):
    try:
        config_path = Path('configuration.yml')
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
                
            # Update dynamic cities section
            if 'dynamicCities' not in config:
                config['dynamicCities'] = {}
            
            config['dynamicCities']['enabled'] = True
            if is_first_batch:
                config['dynamicCities']['previousBatch'] = []
            else:
                config['dynamicCities']['previousBatch'] = config['dynamicCities'].get('current', [])
            config['dynamicCities']['current'] = cities
            
            # Write updated config
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
                
            return True
    except Exception as e:
        # print(f"Error updating configuration: {str(e)}")
        pass
        return False

# Get configuration helper function
def get_configuration():
    """Read and return the configuration from configuration.yml file"""
    try:
        config_path = Path('configuration.yml')
        if not config_path.exists():
            # print("Configuration file not found")
            return {}

        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        # print(f"Error reading configuration: {str(e)}")
        return {}

# Execute country cities script function
async def execute_country_cities_script(country: str) -> dict:
    """Execute the countryCities.sh script to fetch city data for a given country."""
    try:
        # Make the script executable
        script_path = '/app/city-api/countryCities.sh'
        os.chmod(script_path, 0o755)
        
        # Execute the script with the country as argument
        process = await asyncio.create_subprocess_exec(
            script_path,
            country,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            # print(f"Script execution failed with error: {stderr.decode()}")
            return {"success": False, "error": "Failed to fetch country data"}
            
        # Parse the JSON output
        try:
            result = json.loads(stdout.decode())
            return result
        except json.JSONDecodeError as e:
            # print(f"Failed to parse script output: {e}")
            return {"success": False, "error": "Failed to parse country data"}
            
    except Exception as e:
        # print(f"Error executing country cities script: {str(e)}")
        return {"success": False, "error": str(e)}

# Get city coordinate function
async def get_city_coordinate(city_name):
    """Get coordinates for a city from an external service (fallback method)"""
    try:
        # Call to geocoding service (replace with your preferred service)
        # This is just an example implementation - you may want to use a real geocoding API
        
        # First try to get from Nominatim
        city_name_encoded = city_name.replace(" ", "+")
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://nominatim.openstreetmap.org/search?q={city_name_encoded}&format=json&limit=1",
                headers={"User-Agent": "GlobalCityStreaming/1.0"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        # print(f"DEBUG: External API found coordinates for '{city_name}'")
                        return {
                            "latitude": float(data[0]["lat"]),
                            "longitude": float(data[0]["lon"])
                        }
        
        # print(f"DEBUG: External API could not find coordinates for city: {city_name}")
        return None
    except Exception as e:
        # print(f"Error getting coordinates for {city_name}: {str(e)}")
        return None

