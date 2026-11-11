# Results

Fill this in **only with numbers from your own runs**. Delete this line once it is complete.

Run date: `YYYY-MM-DD` · Workspace: Databricks Free Edition (serverless)

## 1. Data generated (notebook 01)

| Metric | Value |
| --- | --- |
| Batches / rows written | |
| Labelled fraud rows (share) | |
| Share of rows on hot merchant `M00001` | |

## 2. Pipeline data quality (pipeline event log / Data quality tab)

| Expectation | Records failed | Action |
| --- | --- | --- |
| `positive_amount` | | dropped |
| `card_present` | | dropped |
| `known_currency` | | warned |
| Duplicates removed | | |

Rows: Bronze ___ → Silver ___ → Gold transaction features ___

## 3. Skew fix (notebook 03)

| Run | Duration | Longest task vs median (Spark UI) |
| --- | --- | --- |
| Before | | |
| Fix A · AQE | | |
| Fix B · salting | | |

What I observed: _(one or two sentences in your own words)_

## 4. Fraud model (notebook 04, MLflow run)

| Metric | Value |
| --- | --- |
| Average precision | |
| Precision @ 0.5 | |
| Recall @ 0.5 | |
| Registered version | `fraud.ml.card_fraud_model` v__ @champion |

What I would improve next: _(your own words)_

## 5. Problems I hit and how I fixed them

_(This is the most valuable section for interviews. Write down real errors and fixes as they happen.)_

- 
