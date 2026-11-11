-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 02 · Governance: mask card IDs for non-privileged users
-- MAGIC Members of `fraud_admins` see the full card ID; everyone else sees only the last 4 characters.
-- MAGIC Screenshot idea: run the final query as two different users (or before/after adding yourself to the group).
-- MAGIC
-- MAGIC Note: column masks apply to regular tables. If your pipeline tables are streaming tables /
-- MAGIC materialized views, create the masked copy below (CTAS) or apply the mask via the pipeline's table definition.

-- COMMAND ----------

CREATE OR REPLACE FUNCTION fraud.gov.mask_card(card STRING)
RETURN CASE
  WHEN is_account_group_member('fraud_admins') THEN card
  ELSE concat('XXXX', right(card, 4))
END;

-- COMMAND ----------

CREATE OR REPLACE TABLE fraud.gold.analyst_transactions AS
SELECT txn_id, card_id, merchant_id, mcc, amount, city, channel, txn_ts, is_fraud
FROM fraud.silver.silver_transactions;

-- COMMAND ----------

ALTER TABLE fraud.gold.analyst_transactions
  ALTER COLUMN card_id SET MASK fraud.gov.mask_card;

-- COMMAND ----------

SELECT card_id, amount, city, is_fraud
FROM fraud.gold.analyst_transactions
LIMIT 10;
