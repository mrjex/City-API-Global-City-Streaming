from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Import routers
from routes import monitoring, proxy, config, country, cache, location
from utils.endpoint_utils import start_control_consumer
from core.globals import dynamic_cities

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(monitoring.router)
app.include_router(proxy.router)
app.include_router(config.router)
app.include_router(country.router)
app.include_router(cache.router)
app.include_router(location.router)

# Start the control consumer when the app starts
@app.on_event("startup")
async def startup_event():
    start_control_consumer(dynamic_cities)