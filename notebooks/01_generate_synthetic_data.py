# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Generate synthetic card transactions
# MAGIC Writes fake transactions as JSON-lines files into the landing volume, in several
# MAGIC batches, so Auto Loader in the pipeline picks them up incrementally.
# MAGIC
# MAGIC **All data is synthetic.** Never load real customer or employer data.

# COMMAND ----------

import os
import sys
from datetime import datetime, timedelta

import pandas as pd

# Make src/ importable when this repo is opened as a Databricks Git folder
repo_root = os.path.dirname(os.getcwd())
sys.path.insert(0, os.path.join(repo_root, "src"))

from fraud_lib.synthetic_data import generate_transactions, inject_bad_records

# COMMAND ----------

dbutils.widgets.text("catalog", "fraud")
dbutils.widgets.text("batches", "5")
dbutils.widgets.text("rows_per_batch", "20000")

catalog = dbutils.widgets.get("catalog")
batches = int(dbutils.widgets.get("batches"))
rows_per_batch = int(dbutils.widgets.get("rows_per_batch"))
landing = f"/Volumes/{catalog}/raw/landing/transactions"
os.makedirs(landing, exist_ok=True)

# COMMAND ----------

for b in range(batches):
    rows = generate_transactions(n=rows_per_batch, seed=100 + b,
                                 start=datetime(2026, 1, 1) + timedelta(days=30 * b))
    rows = inject_bad_records(rows, n_bad=100, seed=200 + b)
    path = f"{landing}/batch_{b:03d}.json"
    pd.DataFrame(rows).to_json(path, orient="records", lines=True)
    print(f"wrote {len(rows):,} rows -> {path}")

# COMMAND ----------

# Quick check of what landed (record these numbers in docs/RESULTS.md)
df = spark.read.json(landing)
display(df.groupBy("is_fraud").count())
display(df.groupBy("merchant_id").count().orderBy("count", ascending=False).limit(5))
