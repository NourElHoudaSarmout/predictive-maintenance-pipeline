# Databricks notebook source
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score

OUTPUT = "/Volumes/workspace/default/sensor_volume/predictions.csv"

df = spark.read.table("sensor_features").toPandas()
df = df.sort_values("timestamp").reset_index(drop=True)

# the model only sees the engineered features, never the label
features = [c for c in df.columns if c.endswith(("_avg", "_std", "_change"))]
print(len(df), "rows,", len(features), "features")

# COMMAND ----------

# contamination = how many readings the model should flag as abnormal.
# is_anomaly is only used here to check the result, not to train.
for contamination in [0.03, 0.06, 0.10]:
    model = IsolationForest(contamination=contamination, random_state=42)
    model.fit(df[features])
    flagged = (model.predict(df[features]) == -1).astype(int)
    print(
        contamination,
        "precision:", round(precision_score(df["is_anomaly"], flagged), 2),
        "recall:", round(recall_score(df["is_anomaly"], flagged), 2),
    )

# COMMAND ----------

# 0.06 gave the best balance between missed faults and false alarms
model = IsolationForest(contamination=0.06, random_state=42)
model.fit(df[features])

df["predicted_anomaly"] = (model.predict(df[features]) == -1).astype(int)
df["score"] = -model.decision_function(df[features])  # higher = more abnormal

columns = [
    "timestamp", "temperature_c", "vibration_mm_s", "speed_rpm",
    "is_anomaly", "predicted_anomaly", "score",
]
df[columns].to_csv(OUTPUT, index=False)
print("saved", OUTPUT)
