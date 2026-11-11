-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 00 · Set up the Unity Catalog objects
-- MAGIC Creates the catalog, the medallion schemas and a volume for raw landing files.
-- MAGIC Run once. In Databricks Free Edition you may need to use the default `workspace`
-- MAGIC catalog instead of creating a new one; if so, replace `fraud` with `workspace` below
-- MAGIC and in `databricks.yml`.

-- COMMAND ----------

CREATE CATALOG IF NOT EXISTS fraud;

-- COMMAND ----------

CREATE SCHEMA IF NOT EXISTS fraud.raw    COMMENT 'Landing zone for raw files';
CREATE SCHEMA IF NOT EXISTS fraud.bronze COMMENT 'Raw data as ingested';
CREATE SCHEMA IF NOT EXISTS fraud.silver COMMENT 'Validated, de-duplicated data';
CREATE SCHEMA IF NOT EXISTS fraud.gold   COMMENT 'Business features and KPIs';
CREATE SCHEMA IF NOT EXISTS fraud.ml     COMMENT 'Models';
CREATE SCHEMA IF NOT EXISTS fraud.gov    COMMENT 'Governance functions (masks, filters)';

-- COMMAND ----------

CREATE VOLUME IF NOT EXISTS fraud.raw.landing COMMENT 'Synthetic card-transaction JSON files';

-- COMMAND ----------

SHOW SCHEMAS IN fraud;
