FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    dos2unix \
    curl \
    jq \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && wget https://github.com/mikefarah/yq/releases/download/v4.40.5/yq_linux_amd64 -O /usr/bin/yq \
    && chmod +x /usr/bin/yq

WORKDIR /app

# Copy requirements first and install all Python dependencies at once
COPY city-api/requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy all application files first
COPY configuration.yml /app/
COPY city-api/ /app/

# Create necessary directories
RUN mkdir -p \
    /app/generated-artifacts/csvs \
    /app/generated-artifacts/charts \
    /app/generated-artifacts/pngs/equator-chart/none-filter-queries \
    /app/generated-artifacts/pngs/equator-chart/continent-queries \
    /app/generated-artifacts/pngs/equator-chart/timezone-queries \
    /app/chart-helpers \
    /app/apis/database \
    /app/apis/database/logs \
    && chmod +x /app/equatorChart.sh \
    && chmod +x /app/countryCities.sh \
    && chmod +x /app/realTimeCharts.sh

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8003

# Expose the FastAPI port
EXPOSE 8003

# Start the FastAPI server
CMD ["python3", "-c", "import sys; sys.path.insert(0, '/app'); import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8003)"]