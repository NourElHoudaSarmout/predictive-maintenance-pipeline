"""
Uploads the generated sensor data CSV to Azure Blob Storage.

This mimics how a real machine's edge gateway would push batches of
sensor readings up to the cloud for central processing.

Setup (one-time, in the Azure Portal):
1. Create a Storage Account (Standard, LRS is fine and cheapest).
2. Inside it, create a Container named "sensor-data" (Access level: Private).
3. Go to "Access keys" on the storage account and copy a connection string.
4. Set it as an environment variable (never hardcode it):
       export AZURE_STORAGE_CONNECTION_STRING="<paste-here>"

Run:
    python upload_to_blob.py
"""

import os
import sys
from datetime import datetime, timezone

from azure.storage.blob import BlobServiceClient

CONTAINER_NAME = "sensor-data"
LOCAL_FILE_PATH = os.environ.get("OUTPUT_PATH", "../data/sensor_data.csv")


def get_blob_service_client() -> BlobServiceClient:
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        sys.exit(
            "Missing AZURE_STORAGE_CONNECTION_STRING environment variable.\n"
            "Set it to your storage account's connection string before running this script."
        )
    return BlobServiceClient.from_connection_string(connection_string)


def ensure_container_exists(service_client: BlobServiceClient, container_name: str) -> None:
    container_client = service_client.get_container_client(container_name)
    if not container_client.exists():
        container_client.create_container()
        print(f"Created container '{container_name}'")


def upload_file(service_client: BlobServiceClient, local_path: str) -> str:
    # Name the blob with a timestamp so repeated runs don't overwrite each other,
    # similar to how a real machine would upload one file per batch/shift.
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    blob_name = f"sensor_data_{timestamp}.csv"

    blob_client = service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    with open(local_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    return blob_name


if __name__ == "__main__":
    if not os.path.exists(LOCAL_FILE_PATH):
        sys.exit(
            f"File not found: {LOCAL_FILE_PATH}\n"
            "Run generate_sensor_data.py first to create it."
        )

    client = get_blob_service_client()
    ensure_container_exists(client, CONTAINER_NAME)
    uploaded_name = upload_file(client, LOCAL_FILE_PATH)

    print(f"Uploaded '{LOCAL_FILE_PATH}' -> container '{CONTAINER_NAME}' as '{uploaded_name}'")
