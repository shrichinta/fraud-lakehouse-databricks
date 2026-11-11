"""Lakeflow Declarative Pipeline: Bronze -> Silver -> Gold for card transactions.

Attach this file to a pipeline (or deploy it with databricks.yml).
Pipeline configuration key `landing_path` must point at the landing volume, e.g.
/Volumes/fraud/raw/landing/transactions
"""

import dlt
from pyspark.sql import functions as F
from pyspark.sql.window import Window

LANDING = spark.conf.get("landing_path", "/Volumes/fraud/raw/landing/transactions")


# ---------------- Bronze: raw, append-only, replayable ----------------
@dlt.table(
    name="bronze_transactions",
    comment="Raw card transactions as ingested by Auto Loader",
    table_properties={"quality": "bronze"},
)
def bronze_transactions():
    return (
        spark.readStream.format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .load(LANDING)
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.col("_metadata.file_path"))
    )


# ---------------- Silver: validated + de-duplicated ----------------
@dlt.table(
    name="silver_transactions",
    comment="Validated, typed, de-duplicated transactions",
    table_properties={"quality": "silver"},
)
@dlt.expect_or_drop("positive_amount", "amount > 0")
@dlt.expect_or_drop("card_present", "card_id IS NOT NULL")
@dlt.expect("known_currency", "currency = 'INR'")  # warn only, keep the row
def silver_transactions():
    return (
        dlt.read_stream("bronze_transactions")
        .withColumn("txn_ts", F.to_timestamp("txn_time"))
        .withColumn("amount", F.col("amount").cast("decimal(12,2)"))
        .withWatermark("txn_ts", "1 day")
        .dropDuplicates(["txn_id", "txn_ts"])
        .drop("_rescued_data")
    )


# ---------------- Gold: features for the fraud model ----------------
@dlt.table(
    name="gold_card_daily_features",
    comment="Daily spend behaviour per card",
    table_properties={"quality": "gold"},
)
def gold_card_daily_features():
    return (
        dlt.read("silver_transactions")
        .groupBy("card_id", F.to_date("txn_ts").alias("txn_date"))
        .agg(
            F.count("*").alias("txn_count"),
            F.sum("amount").alias("total_spend"),
            F.max("amount").alias("max_amount"),
            F.countDistinct("merchant_id").alias("merchant_count"),
            F.countDistinct("city").alias("city_count"),
        )
    )


@dlt.table(
    name="gold_transaction_features",
    comment="Per-transaction features used to train and score the fraud model",
    table_properties={"quality": "gold"},
)
def gold_transaction_features():
    txns = dlt.read("silver_transactions")
    by_card_time = Window.partitionBy("card_id").orderBy(F.col("txn_ts").cast("long"))
    last_hour = by_card_time.rangeBetween(-3600, 0)
    last_day = by_card_time.rangeBetween(-86400, 0)
    home = (txns.groupBy("card_id", "city").count()
                .withColumn("rn", F.row_number().over(
                    Window.partitionBy("card_id").orderBy(F.desc("count"))))
                .filter("rn = 1").select("card_id", F.col("city").alias("home_city")))
    return (
        txns.join(home, "card_id", "left")
        .withColumn("txn_count_1h", F.count("*").over(last_hour))
        .withColumn("spend_24h", F.sum("amount").over(last_day))
        .withColumn("avg_amount_24h", F.avg("amount").over(last_day))
        .withColumn("amount_vs_avg", F.col("amount") / F.col("avg_amount_24h"))
        .withColumn("is_away_from_home", (F.col("city") != F.col("home_city")).cast("int"))
        .withColumn("is_risky_mcc", F.col("mcc").isin("7995", "5967", "4829", "6051").cast("int"))
        .withColumn("hour_of_day", F.hour("txn_ts"))
        .select("txn_id", "card_id", "merchant_id", "txn_ts", "amount", "txn_count_1h",
                "spend_24h", "amount_vs_avg", "is_away_from_home", "is_risky_mcc",
                "hour_of_day", "channel", "is_fraud")
    )


@dlt.table(name="gold_fraud_kpis", comment="Daily fraud KPIs for dashboards")
def gold_fraud_kpis():
    return (
        dlt.read("silver_transactions")
        .groupBy(F.to_date("txn_ts").alias("txn_date"))
        .agg(
            F.count("*").alias("transactions"),
            F.sum("is_fraud").alias("fraud_transactions"),
            F.sum(F.when(F.col("is_fraud") == 1, F.col("amount"))).alias("fraud_amount"),
        )
        .withColumn("fraud_rate", F.col("fraud_transactions") / F.col("transactions"))
    )
