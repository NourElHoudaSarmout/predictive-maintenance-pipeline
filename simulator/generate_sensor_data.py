"""
Sensor data simulator for a packaging machine.

Simulates three sensors (temperature, vibration, speed) sampled once per
second, mimicking readings you'd get from a real machine's PLC/OPC UA
interface. Occasionally injects an anomaly window (a developing fault)
so there is something for the downstream ML model to detect.

The `is_anomaly` column is written for evaluation purposes only -- in a
real / unsupervised setting you would not have this label available.
"""

import csv
import os
import random
from datetime import datetime, timedelta

# ---- configuration -----------------------------------------------------

NUM_ROWS = 10_000          # ~2.75 hours of data at 1 reading/sec
ANOMALY_PROBABILITY = 0.0015   # chance an anomaly window *starts* on a given row
ANOMALY_DURATION_RANGE = (20, 60)  # seconds an anomaly window lasts
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "../data/sensor_data.csv")

BASELINE = {
    "temperature_c": 45.0,   # normal operating temperature
    "vibration_mm_s": 2.0,   # normal vibration velocity
    "speed_rpm": 1200.0,     # normal motor speed
}

NOISE_STD = {
    "temperature_c": 0.4,
    "vibration_mm_s": 0.15,
    "speed_rpm": 8.0,
}

# how much each sensor drifts during an anomaly (added on top of baseline)
ANOMALY_SHIFT = {
    "temperature_c": 18.0,
    "vibration_mm_s": 4.5,
    "speed_rpm": -60.0,
}


def generate_row(timestamp: datetime, in_anomaly: bool, progress: float) -> dict:
    """Generate one row of sensor readings.

    progress is 0->1 through the anomaly window, used to ramp the fault
    in and out gradually rather than as a hard step change.
    """
    row = {"timestamp": timestamp.isoformat()}

    ramp = 0.0
    if in_anomaly:
        # ramp up then hold: simple triangular ramp for realism
        ramp = min(progress * 2, 1.0) if progress < 0.5 else min((1 - progress) * 2 + 0.6, 1.0)

    for sensor, baseline in BASELINE.items():
        noise = random.gauss(0, NOISE_STD[sensor])
        shift = ANOMALY_SHIFT[sensor] * ramp
        row[sensor] = round(baseline + shift + noise, 2)

    row["is_anomaly"] = int(in_anomaly)
    return row


def generate_dataset(num_rows: int) -> list[dict]:
    rows = []
    start = datetime(2026, 1, 1, 6, 0, 0)

    anomaly_remaining = 0
    anomaly_length = 0

    for i in range(num_rows):
        timestamp = start + timedelta(seconds=i)

        if anomaly_remaining == 0 and random.random() < ANOMALY_PROBABILITY:
            anomaly_length = random.randint(*ANOMALY_DURATION_RANGE)
            anomaly_remaining = anomaly_length

        in_anomaly = anomaly_remaining > 0
        progress = 1 - (anomaly_remaining / anomaly_length) if in_anomaly else 0.0

        rows.append(generate_row(timestamp, in_anomaly, progress))

        if anomaly_remaining > 0:
            anomaly_remaining -= 1

    return rows


def write_csv(rows: list[dict], path: str) -> None:
    fieldnames = ["timestamp", "temperature_c", "vibration_mm_s", "speed_rpm", "is_anomaly"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    random.seed(42)  # reproducible dataset
    dataset = generate_dataset(NUM_ROWS)
    write_csv(dataset, OUTPUT_PATH)

    anomaly_count = sum(r["is_anomaly"] for r in dataset)
    print(f"Generated {len(dataset)} rows -> {OUTPUT_PATH}")
    print(f"Anomalous rows: {anomaly_count} ({anomaly_count / len(dataset):.2%})")
