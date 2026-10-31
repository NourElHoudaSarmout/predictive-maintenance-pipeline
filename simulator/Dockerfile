# Lightweight image just for running the sensor data simulator.
# Build:  docker build -t sensor-simulator .
# Run:    docker run --rm -v $(pwd)/../data:/data sensor-simulator

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY generate_sensor_data.py upload_to_blob.py .

# Output path inside the container maps to the mounted /data volume
ENV OUTPUT_PATH=/data/sensor_data.csv

# Default command just generates data; override with upload_to_blob.py
# when you want to push it to Azure, e.g.:
#   docker run --rm -v $(pwd)/../data:/data \
#     -e AZURE_STORAGE_CONNECTION_STRING="..." \
#     sensor-simulator python upload_to_blob.py
CMD ["python", "generate_sensor_data.py"]
