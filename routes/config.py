from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import yaml
from pathlib import Path
import os
import subprocess
from utils.endpoint_utils import get_kafka_producer, CONTROL_TOPIC

router = APIRouter()

@router.get("/api/config")
async def get_config():
    try:
        config_path = Path('configuration.yml')
        if not config_path.exists():
            return JSONResponse(
                content={"error": "Configuration file not found"},
                status_code=500
            )

        with open(config_path) as f:
            config = yaml.safe_load(f)
        return JSONResponse(content=config)
    except Exception as e:
        return JSONResponse(
            content={"error": "Failed to read configuration"},
            status_code=500
        )

@router.post("/api/config")
async def update_config(request: Request):
    try:
        body = await request.json()
        config_path = Path('configuration.yml')
        
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
        else:
            config = {}
            
        path = body.get('path', '').split('.')
        current = config
        for part in path[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[path[-1]] = body.get('config')
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)

        if path[0] == 'dynamicCities':
            try:
                producer = get_kafka_producer()
                new_cities = body.get('config', {}).get('current', [])
                control_message = {
                    'action': 'UPDATE_CITIES',
                    'data': {
                        'cities': new_cities
                    }
                }
                producer.send(CONTROL_TOPIC, value=control_message)
                producer.flush()
            except Exception:
                pass

        script_path = Path('/app/city-api/equatorChart.sh')
        figure_json = None
        
        print(f"CHART_LOG: Script exists: {script_path.exists()}")
        
        if script_path.exists():
            print("CHART_LOG: Executing equator chart script...")
            try:
                os.chmod('/app/city-api/equatorChart.sh', 0o755)
                result = subprocess.run(['/bin/sh', '/app/city-api/equatorChart.sh'], capture_output=True, text=True)
                print(f"CHART_LOG: Script exit code: {result.returncode}")
                print(f"CHART_LOG: Script stdout length: {len(result.stdout)}")
                print(f"CHART_LOG: Script stderr length: {len(result.stderr)}")
                
                response_json_path = Path('/app/city-api/apis/database/response.json')
                if response_json_path.exists():
                    with open(response_json_path, 'r') as f:
                        response_content = f.read()
                    print(f"CHART_LOG: response.json length: {len(response_content)}")
                    print(f"CHART_LOG: response.json content: {response_content[:100]}...")
                else:
                    print(f"CHART_LOG: response.json does not exist at {response_json_path}")
                
                output = result.stdout
                if "FIGURE_JSON_START" in output and "FIGURE_JSON_END" in output:
                    json_str = output[output.find("FIGURE_JSON_START") + len("FIGURE_JSON_START"):output.find("FIGURE_JSON_END")].strip()
                    figure_json = json_str
                    print("CHART_LOG: Successfully captured figure JSON")
                else:
                    print("CHART_LOG: Could not find figure JSON in output")
                
                if result.returncode != 0:
                    print(f"CHART_LOG: Warning: equatorChart.sh exited with code {result.returncode}")
                    print(f"CHART_LOG: Script stderr: {result.stderr}")
            except Exception as e:
                print(f"CHART_LOG: Error executing equator chart script: {str(e)}")
        else:
            print(f"CHART_LOG: Warning: Script not found at {script_path}")
            
        return JSONResponse(content={
            "success": True,
            "figure": figure_json
        })
    except Exception as e:
        print(f"CHART_LOG: Error updating configuration: {str(e)}")
        return JSONResponse(
            content={"error": "Failed to update configuration"},
            status_code=500
        ) 