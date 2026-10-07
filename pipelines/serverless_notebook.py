# Databricks notebook source
# Thin entrypoint for an existing Serverless notebook / Databricks Git folder.
# Install the declared pipeline requirements once in the notebook environment;
# this notebook has no per-run ad-hoc package installation commands.
# It does not need an external workspace token, warehouse ID, or cluster ID.

# COMMAND ----------
from pathlib import Path
import sys

dbutils.widgets.text("repository_root", str(Path.cwd().parent))
dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema_prefix", "olist")
dbutils.widgets.text("raw_volume", "raw")
dbutils.widgets.text("batch_end", "")

# COMMAND ----------
root = Path(dbutils.widgets.get("repository_root"))
if not (root / "src" / "olist").is_dir():
    raise ValueError("Set repository_root to the actual Databricks Git folder checkout root")
sys.path[:0] = [str(root), str(root / "src")]
from olist.config import Config
from pipelines.databricks_job import execute

config = Config(catalog=dbutils.widgets.get("catalog"),
                prefix=dbutils.widgets.get("schema_prefix"),
                volume=dbutils.widgets.get("raw_volume"))
audit = execute(spark, config, batch_end=dbutils.widgets.get("batch_end") or None)
print(audit)
