# CrisisFlow Fabric Notebook — Emergency Analytics
# ═══════════════════════════════════════════════════
# Run this notebook in Microsoft Fabric to analyze emergency data.
# It connects to the CrisisFlow Lakehouse for historical analysis.

# %% [markdown]
# # 🚨 CrisisFlow Emergency Analytics Notebook
# This notebook performs:
# - Historical incident analysis
# - Response time calculations
# - Resource utilization metrics
# - Risk zone scoring
# - Basic severity prediction

# %% Setup
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import matplotlib.pyplot as plt

spark = SparkSession.builder.getOrCreate()

# %% Load Data from Lakehouse
# These tables are populated by the CrisisFlow Eventstream → Lakehouse pipeline
incidents_df = spark.read.format("delta").load("Tables/FactIncidents")
dispatches_df = spark.read.format("delta").load("Tables/FactDispatches")
resources_df = spark.read.format("delta").load("Tables/FactResourceEvents")
hospitals_df = spark.read.format("delta").load("Tables/FactHospitalEvents")

# %% Incident Analysis
print("=== INCIDENT ANALYSIS ===")
print(f"Total Incidents: {incidents_df.count()}")

# By type
incidents_df.groupBy("incident_type").count().orderBy(desc("count")).show()

# By severity
incidents_df.groupBy("severity").count().orderBy(desc("count")).show()

# Critical incidents
critical = incidents_df.filter(col("severity") == "Critical")
print(f"Critical Incidents: {critical.count()}")

# %% Response Time Analysis
print("=== RESPONSE TIME ANALYSIS ===")
dispatches_df.select(
    avg("eta_minutes").alias("avg_response_time"),
    min("eta_minutes").alias("min_response_time"),
    max("eta_minutes").alias("max_response_time"),
).show()

# Response time by incident type
dispatches_df.join(incidents_df, "incident_id") \
    .groupBy("incident_type") \
    .agg(avg("eta_minutes").alias("avg_response_time")) \
    .orderBy("avg_response_time") \
    .show()

# %% Resource Utilization
print("=== RESOURCE UTILIZATION ===")
resources_df.groupBy("resource_type", "status") \
    .count() \
    .orderBy("resource_type", desc("count")) \
    .show()

# %% Hospital Capacity Analysis
print("=== HOSPITAL CAPACITY ===")
hospitals_df.groupBy("hospital_name") \
    .agg(
        avg("occupancy").alias("avg_occupancy"),
        max("occupancy").alias("peak_occupancy"),
    ) \
    .orderBy(desc("avg_occupancy")) \
    .show()

# %% Risk Zone Scoring
# Simple risk score based on incident frequency and severity
risk_scores = incidents_df \
    .groupBy("location") \
    .agg(
        count("*").alias("incident_count"),
        sum(when(col("severity") == "Critical", 4)
            .when(col("severity") == "High", 3)
            .when(col("severity") == "Medium", 2)
            .otherwise(1)).alias("severity_score"),
        sum("people_at_risk").alias("total_people_at_risk"),
    ) \
    .withColumn("risk_score",
        (col("incident_count") * 10 + col("severity_score") * 5 + col("total_people_at_risk") * 0.5)) \
    .orderBy(desc("risk_score"))

print("=== HIGH RISK LOCATIONS ===")
risk_scores.show(10)

# %% Simple Severity Prediction Model
# Uses basic features to predict incident severity
from pyspark.ml.feature import VectorAssembler, StringIndexer
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml import Pipeline

# Prepare features
indexer = StringIndexer(inputCol="incident_type", outputCol="type_index")
assembler = VectorAssembler(
    inputCols=["type_index", "people_at_risk"],
    outputCol="features"
)
label_indexer = StringIndexer(inputCol="severity", outputCol="label")

rf = RandomForestClassifier(numTrees=20, maxDepth=5)

pipeline = Pipeline(stages=[indexer, label_indexer, assembler, rf])

# Only train if we have enough data
if incidents_df.count() > 20:
    train, test = incidents_df.randomSplit([0.8, 0.2])
    model = pipeline.fit(train)
    predictions = model.transform(test)
    accuracy = predictions.filter(col("prediction") == col("label")).count() / predictions.count()
    print(f"Severity Prediction Accuracy: {accuracy:.2%}")
else:
    print("Insufficient data for ML training. Need 20+ incidents.")

# %% Summary
print("\n" + "="*50)
print("🚨 CRISISFLOW ANALYTICS SUMMARY")
print("="*50)
print(f"Total Incidents Analyzed: {incidents_df.count()}")
print(f"Total Dispatches: {dispatches_df.count()}")
print(f"High-Risk Locations: {risk_scores.filter(col('risk_score') > 50).count()}")
print("="*50)
