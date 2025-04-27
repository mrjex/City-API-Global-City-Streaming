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

# Copy application files
COPY city-api/ /app/city-api/
COPY configuration.yml /app/

# Create necessary directories
RUN mkdir -p \
    /app/city-api/generated-artifacts/csvs \
    /app/city-api/generated-artifacts/charts \
    /app/city-api/generated-artifacts/pngs/equator-chart/none-filter-queries \
    /app/city-api/generated-artifacts/pngs/equator-chart/continent-queries \
    /app/city-api/generated-artifacts/pngs/equator-chart/timezone-queries \
    /app/city-api/chart-helpers \
    /app/city-api/apis/database \
    /app/city-api/apis/database/logs

# Make scripts executable
RUN chmod +x /app/city-api/equatorChart.sh
RUN chmod +x /app/city-api/countryCities.sh
RUN chmod +x /app/city-api/realTimeCharts.sh 2>/dev/null || true

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8003

# Expose the FastAPI port
EXPOSE 8003

# Start the FastAPI server
CMD ["python", "-m", "uvicorn", "city-api.main:app", "--host", "0.0.0.0", "--port", "8003"] 