# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Reproduce and fix data skew
# MAGIC `M00001` receives ~40% of transactions, so a join on `merchant_id` puts most rows in one partition.
# MAGIC
# MAGIC 1. Run **Before** with AQE skew handling off, open the Spark UI → Stages, and screenshot the one long task.
# MAGIC 2. Run **Fix A (AQE)** and **Fix B (salting)**, screenshot the even task times.
# MAGIC 3. Record the durations in `docs/RESULTS.md`.
# MAGIC
# MAGIC On serverless compute some Spark configs cannot be changed; if `spark.conf.set` fails,
# MAGIC skip to Fix B, which works anywhere.

# COMMAND ----------

import time
from pyspark.sql import functions as F

txns = spark.table("fraud.silver.silver_transactions")
merchants = (txns.select("merchant_id").distinct()
                 .withColumn("merchant_risk", (F.rand(seed=1) * 100).cast("int")))

def timed(label, df):
    t0 = time.time()
    n = df.count()
    print(f"{label}: {n:,} rows in {time.time() - t0:.1f}s")

display(txns.groupBy("merchant_id").count().orderBy(F.desc("count")).limit(5))

# COMMAND ----------

# Before: plain sort-merge join, AQE skew handling and broadcast disabled
for k, v in {"spark.sql.adaptive.skewJoin.enabled": "false",
             "spark.sql.autoBroadcastJoinThreshold": "-1"}.items():
    try:
        spark.conf.set(k, v)
    except Exception as e:
        print(f"could not set {k}: {e}")

timed("Before (skewed join)", txns.join(merchants, "merchant_id"))

# COMMAND ----------

# Fix A: let Adaptive Query Execution split the skewed partition
try:
    spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
except Exception as e:
    print(e)
timed("Fix A (AQE skew join)", txns.join(merchants, "merchant_id"))

# COMMAND ----------

# Fix B: salt the hot key so it spreads across SALT partitions
SALT = 16
txns_salted = txns.withColumn("salt", (F.rand(seed=7) * SALT).cast("int"))
merchants_salted = merchants.withColumn("salt", F.explode(F.array([F.lit(i) for i in range(SALT)])))
timed("Fix B (salting)", txns_salted.join(merchants_salted, ["merchant_id", "salt"]).drop("salt"))
