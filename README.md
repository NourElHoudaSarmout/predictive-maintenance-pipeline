# Predictive maintenance pipeline

A small project that simulates a packaging machine, detects abnormal sensor
behavior with machine learning, and shows the result on a dashboard.

I built it to practice the path from machine data to a usable cloud product:
getting data into the cloud, applying AI, and presenting it to people who
are not developers. The data is simulated, but the pipeline is real.

## How it works

```
Python simulator -> Azure Blob Storage -> Databricks (PySpark + Isolation Forest)
                                                     |
                                          predictions.csv
                                                     |
                                    .NET API -> React dashboard
```

1. **Simulator** (`simulator/`): generates one reading per second for
   temperature, vibration and speed. Faults start gradually, like real wear.
   Runs in Docker.
2. **Azure Blob Storage**: `upload_to_blob.py` uploads the CSV.
3. **Feature engineering** (`notebooks/feature_engineering.py`): Databricks
   window functions compute a 10-second rolling average, rolling standard
   deviation and rate of change for each sensor.
4. **Model** (`notebooks/train_model.py`): an Isolation Forest finds unusual
   readings without using labels. The simulated labels are only used to
   check the result.
5. **API** (`api/`): a small ASP.NET Core API serves the predictions.
6. **Dashboard** (`dashboard/`): a React page with a chart of each sensor,
   with flagged readings in red.

## Results

With contamination set to 0.06, the model found about 70% of the simulated
fault readings, and about 75% of its alerts were real faults. A lower
setting misses most faults and a higher one raises more false alarms.
(Replace these numbers with the ones from your own run.)

## Run it

1. Generate the data: `cd simulator && python generate_sensor_data.py`
2. (Optional) upload it to Azure with `upload_to_blob.py`. It needs the
   `AZURE_STORAGE_CONNECTION_STRING` environment variable.
3. Run the two notebooks in Databricks, then download `predictions.csv`
   into `data/`.
4. Start the API and dashboard:

```
docker compose up --build
```

The dashboard is at http://localhost:3000 and the API at http://localhost:5000.

## Limits

- The data is synthetic, and real machines have more operating modes.
- Data is uploaded in batches, not streamed. For live data I would use
  Azure IoT Hub or Event Hubs.
- A real machine would be read through its PLC (for example over OPC UA).
  There is no PLC or TwinCAT code here.
- The Databricks workspace could not reach Azure Blob Storage because of
  its network settings, so the notebook reads an uploaded copy of the same
  CSV. In production I would use an external location or a private endpoint.
- Predictions are read from a CSV file. A real setup would use a database
  or a model endpoint.
# predictive-maintenance-pipeline
