# Screenshots

Save screenshots from **your own workspace** here as you build, using these file names, then link them from `docs/RESULTS.md`.
Crop out workspace URLs, tokens and email addresses before committing.

| # | File name | What to capture |
| --- | --- | --- |
| 1 | `01_catalog_explorer.png` | Catalog Explorer showing the `fraud` catalog with raw/bronze/silver/gold/ml/gov schemas |
| 2 | `02_pipeline_graph.png` | Pipeline graph bronze → silver → gold with row counts |
| 3 | `03_data_quality.png` | Pipeline data-quality tab showing dropped records per expectation |
| 4 | `04_column_mask.png` | Masked `card_id` values in `analyst_transactions` |
| 5 | `05_lineage.png` | Unity Catalog lineage from bronze to gold |
| 6 | `06_skew_before.png` | Spark UI stage page with one long task |
| 7 | `07_skew_after.png` | Same stage with even task times after the fix |
| 8 | `08_mlflow_runs.png` | MLflow experiment with runs compared on average precision |
| 9 | `09_registered_model.png` | `fraud.ml.card_fraud_model` with the `@champion` alias |
| 10 | `10_github_actions.png` | Green CI/CD run: tests → bundle validate → deploy |
