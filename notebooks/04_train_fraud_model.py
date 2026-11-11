# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Train, track and register the fraud model (week 3)
# MAGIC Reads the Gold feature table, trains a gradient-boosted classifier, logs it to MLflow
# MAGIC and registers it in Unity Catalog as `fraud.ml.card_fraud_model`.
# MAGIC Record the metrics you actually get in `docs/RESULTS.md`.

# COMMAND ----------

import mlflow
import pandas as pd
from mlflow.models import infer_signature
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

mlflow.set_registry_uri("databricks-uc")
MODEL_NAME = "fraud.ml.card_fraud_model"
FEATURES = ["amount", "txn_count_1h", "spend_24h", "amount_vs_avg",
            "is_away_from_home", "is_risky_mcc", "hour_of_day"]

pdf = (spark.table("fraud.silver.gold_transaction_features")
            .select(*FEATURES, "is_fraud").toPandas())
pdf[FEATURES] = pdf[FEATURES].astype(float)
X, y = pdf[FEATURES], pdf["is_fraud"].astype(int)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
print(f"train={len(X_train):,} test={len(X_test):,} fraud share={y.mean():.3%}")

# COMMAND ----------

with mlflow.start_run(run_name="hgb_baseline") as run:
    params = {"max_iter": 200, "learning_rate": 0.1, "max_depth": 6}
    model = HistGradientBoostingClassifier(**params, random_state=42).fit(X_train, y_train)
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= 0.5).astype(int)

    metrics = {
        "avg_precision": average_precision_score(y_test, proba),   # right metric for rare fraud
        "precision_at_0_5": precision_score(y_test, pred, zero_division=0),
        "recall_at_0_5": recall_score(y_test, pred),
    }
    mlflow.log_params(params)
    mlflow.log_metrics(metrics)
    mlflow.sklearn.log_model(
        model, "model",
        signature=infer_signature(X_train, model.predict_proba(X_train)[:, 1]),
        input_example=X_train.head(5),
        registered_model_name=MODEL_NAME,
    )
    print(metrics)

# COMMAND ----------

# Mark the newest version as champion (alias used by the serving endpoint)
from mlflow import MlflowClient
client = MlflowClient()
latest = max(int(v.version) for v in client.search_model_versions(f"name='{MODEL_NAME}'"))
client.set_registered_model_alias(MODEL_NAME, "champion", latest)
print(f"{MODEL_NAME} v{latest} -> @champion")
