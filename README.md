# City API

This repository implements the **City API**, a backend service that aggregates, processes, and serves city-related data from a variety of public APIs. It is designed as a core submodule of the [Global City Streaming](https://github.com/mrjex/Global-City-Streaming) project, providing essential data and functionality to the overall system.

The City API receives its requests primarily from the [Frontend Component](https://github.com/mrjex/Frontend-Global-City-Streaming), acting as the main data provider for city, country, and video information.

## Key Features

- **City and Country Data Aggregation:**
  - Fetches and serves city lists, coordinates, and metadata for countries using multiple public APIs.
  - Provides batch and single-city coordinate lookup endpoints.

- **Video and Description Data:**
  - Supplies video links and descriptions for capital cities and other major cities.

- **Real-Time Data Streaming:**
  - Integrates with [Kafka Producer](https://github.com/mrjex/Kafka-Producer-Global-City-Streaming) and [Flink Processor](https://github.com/mrjex/Flink-Processor-Global-City-Streaming) for real-time temperature and analytics data streaming.
  - Exposes endpoints for raw and database logs from the Flink processor.

- **Caching and Performance:**
  - Uses [Redis](https://github.com/mrjex/Redis-Global-City-Streaming) for caching city, country, and video data to improve response times and reduce redundant API calls.

- **Configuration and Control:**
  - Supports dynamic configuration updates (e.g., changing the set of tracked cities) via API endpoints.
  - Provides health and readiness endpoints for orchestration and monitoring.


## Example Endpoints

- `/api/city-data/{country}` – Get city data for a given country
- `/api/city-coordinates/{city_name}` – Get coordinates for a specific city
- `/api/city-coordinates/batch` – Batch lookup of city coordinates
- `/api/video-data/{country}` – Get video and description data for a country's capital
- `/api/flink-logs/raw` and `/api/flink-logs/db` – Access real-time and historical logs from the Flink processor
- `/api/config` (GET/POST) – Retrieve or update configuration
- `/health` and `/ready` – Health and readiness checks