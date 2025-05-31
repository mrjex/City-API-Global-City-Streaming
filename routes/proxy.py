from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from utils.endpoint_utils import get_docker_client
import json
import re
from core.globals import dynamic_cities

router = APIRouter()

@router.get("/proxy/flink/logs/raw")
async def proxy_flink_raw_logs():
    """
    Proxy endpoint for raw logs from flink processor
    """
    client = get_docker_client()
    if client:
        try:
            container = client.containers.get("flink-processor")
            logs = container.logs(tail=2000).decode("utf-8")
            
            raw_logs = []
            for line in logs.split('\n'):
                if any(pattern in line for pattern in [
                    "Raw data received",
                    "Processing messages",
                    "Connected to Kafka",
                    "Connected to Zookeeper",
                    "Starting Flink job"
                ]):
                    raw_logs.append(line)
            
            filtered_logs = '\n'.join(raw_logs)
            return {"logs": filtered_logs if filtered_logs else ""}
        except Exception as e:
            pass
            return {"logs": ""}
    
    return {"logs": ""}

@router.get("/proxy/flink/logs/db")
async def proxy_flink_db_logs():
    """
    Proxy endpoint for DB logs from flink processor
    """
    client = get_docker_client()
    if client:
        try:
            container = client.containers.get("flink-processor")
            logs = container.logs(tail=2000).decode("utf-8")
            
            db_logs = []
            for line in logs.split('\n'):
                if any(pattern in line for pattern in [
                    "Inserting into DB",
                    "Storing aggregated data",
                    "Connected to PostgreSQL",
                    "database connection"
                ]):
                    db_logs.append(line)
            
            filtered_logs = '\n'.join(db_logs)
            return {"logs": filtered_logs if filtered_logs else ""}
        except Exception as e:
            return {"logs": ""}
    
    return {"logs": ""}

@router.get("/api/flink-logs/raw", response_class=PlainTextResponse)
async def api_flink_raw_logs():
    """
    Frontend-facing endpoint for Flink raw logs.
    Maps to /proxy/flink/logs/raw for consistency.
    """
    return await proxy_flink_raw_logs()

@router.get("/api/flink-logs/db", response_class=PlainTextResponse)
async def api_flink_db_logs():
    """
    Frontend-facing endpoint for Flink DB logs.
    Maps to /proxy/flink/logs/db for consistency.
    """
    return await proxy_flink_db_logs()

@router.get("/api/kafka-logs")
async def get_kafka_logs():
    try:
        client = get_docker_client()
        if client:
            try:
                container = client.containers.get("kafka-producer")
                logs = container.logs(tail=3000).decode("utf-8")
                
                temperature_data = []
                raw_logs = []
                
                for line in logs.split('\n'):
                    raw_logs.append(line)
                    if "Sent data for" in line:
                        try:
                            json_start = line.find('{')
                            if json_start != -1:
                                json_str = line[json_start:]
                                try:
                                    data = json.loads(json_str)
                                    
                                    if data.get('city') in dynamic_cities:
                                        timestamp_match = re.search(r'\[(.*?)\]', line)
                                        timestamp = timestamp_match.group(1) if timestamp_match else None
                                        
                                        if timestamp:
                                            temperature = data.get('temperatureCelsius')
                                            if temperature is not None:
                                                temperature_data.append({
                                                    'city': data['city'],
                                                    'temperature': float(temperature),
                                                    'timestamp': timestamp
                                                })
                                except json.JSONDecodeError:
                                    pass
                        except Exception:
                            continue
                
                return {
                    "logs": "\n".join(raw_logs),
                    "temperatureData": temperature_data,
                    "dynamicCities": dynamic_cities
                }
            except Exception as e:
                return {"error": f"Error accessing kafka-producer container: {str(e)}"}
        else:
            return {"error": "Docker client initialization failed"}
    except Exception as e:
        return {"error": str(e)} 