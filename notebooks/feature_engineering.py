# Databricks notebook source
from pyspark.sql import Window
from pyspark.sql import functions as F

# The same csv that upload_to_blob.py sends to Azure Blob Storage.
# This workspace can't reach the storage account (serverless network
# restrictions), so a copy was uploaded to a Unity Catalog volume instead.
PATH = "/Volumes/workspace/default/sensor_volume/sensor_data.csv"


SENSORS = ["temperature_c", "vibration_mm_s", "speed_rpm"]
WINDOW = 10  # last 10 readings, about 10 seconds

df = spark.read.csv(PATH, header=True, inferSchema=True)
print(df.count(), "rows")

# COMMAND ----------

# rolling average, rolling std and change since the previous reading
w = Window.orderBy("timestamp")
recent = w.rowsBetween(-(WINDOW - 1), 0)

for s in SENSORS:
    df = (
        df.withColumn(f"{s}_avg", F.avg(s).over(recent))
        .withColumn(f"{s}_std", F.stddev(s).over(recent))
        .withColumn(f"{s}_change", F.col(s) - F.lag(s, 1).over(w))
    )

df = df.dropna()  # the first row has no previous value
display(df)

# COMMAND ----------

df.write.mode("overwrite").saveAsTable("sensor_features")