"""Databricks-native batch job: Volume → Spark/Delta → governed SQL application.
Run via bundle job; never execute it against production catalogs for tests.
"""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from olist.config import Config
from olist.ingestion.acquire import land
from olist.ingestion.catalog import SOURCES
from olist.quality.spark_engine import evaluate_spark
from olist.quality.rules import RULES
from olist.quality.engine import readiness, quality_score, FAILURE_COLUMNS
from olist.transformations.spark_models import standardize_spark, gold_spark
from olist.governance.catalog import table_catalog, lineage_catalog
from olist.metrics.definitions import definitions_frame
from olist.pipeline import utcnow
import argparse
import uuid
import pandas as pd


def metadata_frame(spark, frame):
    """Explicit schemas permit empty metadata results and avoid NullType Delta failures."""
    from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, BooleanType
    fields = []
    for col in frame:
        dtype = frame[col].dtype
        typ = BooleanType() if pd.api.types.is_bool_dtype(dtype) else LongType() if pd.api.types.is_integer_dtype(dtype) else DoubleType() if pd.api.types.is_float_dtype(dtype) else StringType()
        fields.append(StructField(col, typ, True))
    rows = []
    for row in frame.itertuples(index=False, name=None):
        values = []
        for value, field in zip(row, fields):
            if pd.isna(value):
                values.append(None)
            elif isinstance(field.dataType, StringType):
                values.append(str(value))
            elif isinstance(field.dataType, LongType):
                values.append(int(value))
            elif isinstance(field.dataType, DoubleType):
                values.append(float(value))
            else:
                values.append(bool(value))
        rows.append(values)
    return spark.createDataFrame(rows, StructType(fields))


def execute(spark, config, batch_end=None, source=None):
    from functools import reduce
    from pyspark.sql import functions as F
    from pyspark.sql.types import StructType, StructField, StringType
    spark.conf.set("spark.sql.session.timeZone", "UTC")
    run_id, started = uuid.uuid4().hex, utcnow()
    audit = {"run_id": run_id, "status": "RUNNING", "started_at": started, "batch_start": "source inception",
             "batch_end": batch_end or "full historical snapshot", "data_label": "REAL OLIST",
             "records_received": 0, "records_processed": 0, "accepted_records": 0,
             "quarantined_records": 0, "failed_checks": 0, "error_message": "", "latest_source_event": "",
             "ended_at": "", "duration_seconds": 0.0}

    def save(layer, name, df):
        df.write.format("delta").mode("append").option("mergeSchema", "true").saveAsTable(config.table(layer, name))

    def audit_write():
        frame = metadata_frame(spark, pd.DataFrame([audit]))
        table = config.table("quality", "pipeline_run_audit")
        if spark.catalog.tableExists(table):
            frame.createOrReplaceTempView("olist_current_audit")
            spark.sql(f"MERGE INTO {table} t USING olist_current_audit s ON t.run_id = s.run_id "
                      "WHEN MATCHED THEN UPDATE SET * WHEN NOT MATCHED THEN INSERT *")
        else:
            frame.write.format("delta").saveAsTable(table)

    for layer in ("bronze", "silver", "gold", "quality"):
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.catalog}.{config.schema(layer)}")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS {config.catalog}.{config.schema('bronze')}.{config.volume}")
    audit_write()
    try:
        land(config.volume_path, source)
        tables = {}
        for ds, spec in SOURCES.items():
            raw = spark.read.option("header", True).option("inferSchema", False).option("multiLine", True).option("escape", '"').option("mode", "FAILFAST").csv(str(config.volume_path / spec.filename))
            # Unique run-local surrogate: preserves repeated identical source rows as separate records.
            raw = raw.withColumn("source_record_id", F.concat(F.lit(f"{ds}:"), F.monotonically_increasing_id().cast("string")))
            tables[ds] = raw
        if batch_end:
            end = str(pd.Timestamp(batch_end))
            original_ids = tables["orders"].select("order_id")
            tables["orders"] = tables["orders"].filter(F.expr("try_cast(order_purchase_timestamp as timestamp)").isNull() | (F.expr("try_cast(order_purchase_timestamp as timestamp)") < F.lit(end).cast("timestamp")))
            eligible = tables["orders"].select("order_id")
            for ds in ("order_items", "payments", "reviews"):
                matched = tables[ds].join(eligible, "order_id", "left_semi")
                orphans = tables[ds].join(original_ids, "order_id", "left_anti")
                tables[ds] = matched.unionByName(orphans)
        for ds, raw in tables.items():
            bronze = raw.withColumn("pipeline_run_id", F.lit(run_id)).withColumn("ingestion_timestamp", F.lit(started)).withColumn("source_file", F.lit(SOURCES[ds].filename)).withColumn("simulated_batch_id", F.lit(batch_end or "full")).withColumn("simulated_batch_start", F.lit("source inception")).withColumn("simulated_batch_end", F.lit(batch_end or "full"))
            save("bronze", ds, bronze)
        # Read governed named Bronze tables to support native lineage capture.
        tables = {ds: spark.table(config.table("bronze", ds)).filter(F.col("pipeline_run_id") == run_id).drop("pipeline_run_id", "ingestion_timestamp", "source_file", "simulated_batch_id", "simulated_batch_start", "simulated_batch_end") for ds in SOURCES}
        results, failures, quarantine, scorecard, accepted = evaluate_spark(tables, run_id, started)
        audit["records_received"] = int(scorecard.source_records.sum())
        audit["records_processed"] = audit["records_received"]
        audit["failed_checks"] = int(results.status.eq("FAILED").sum())
        state = readiness(results)
        silver, cascades = standardize_spark(accepted) if state != "BLOCKED" else ({}, [])
        additional = []
        for ds, parent, frame in cascades:
            count = frame.count()
            if count:
                original = tables[ds].join(frame.select("source_record_id"), "source_record_id", "left_semi")
                additional.append(original.select(F.lit(run_id).alias("run_id"), F.lit(ds).alias("dataset"), "source_record_id", F.lit(f"{ds}.accepted_parent").alias("rule_id"), F.lit("Accepted parent integrity").alias("rule_name"), F.lit("HIGH").alias("severity"), F.lit("QUARANTINE").alias("action"), F.lit(f"Accepted parent missing: {parent}").alias("failure_reason"), F.lit(started).alias("quarantine_timestamp"), F.to_json(F.struct(*[F.col(c) for c in SOURCES[ds].columns])).alias("original_values")))
                scorecard.loc[scorecard.dataset.eq(ds), "accepted_records"] -= count
                scorecard.loc[scorecard.dataset.eq(ds), "quarantined_records"] += count
                scorecard.loc[scorecard.dataset.eq(ds), "readiness"] = "WARNING"
        if additional:
            extra = reduce(lambda a, b: a.unionByName(b), additional)
            failures, quarantine = failures.unionByName(extra), quarantine.unionByName(extra)
            if state == "READY":
                state = "WARNING"
        unique_quarantine = quarantine.select("dataset", "source_record_id").distinct().count()
        audit["quarantined_records"] = unique_quarantine
        audit["accepted_records"] = audit["records_received"] - unique_quarantine
        summary = {"run_id": run_id, "readiness": state, "quality_score": quality_score(results),
                   "quarantined_records": unique_quarantine, "failed_rules": audit["failed_checks"],
                   "data_label": "REAL OLIST", "execution_timestamp": started,
                   "critical_failures": int(((results.severity == "CRITICAL") & results.status.eq("FAILED")).sum())}
        for name, frame in {"dq_rules": pd.DataFrame([r.record() for r in RULES]), "dq_rule_results": results,
                            "dq_dataset_scorecard": scorecard, "dq_run_summary": pd.DataFrame([summary]),
                            "table_catalog": table_catalog(), "metric_dictionary": definitions_frame(), "lineage_edges": lineage_catalog()}.items():
            if "run_id" not in frame:
                frame["run_id"] = run_id
            save("quality", name, metadata_frame(spark, frame))
        save("quality", "dq_failed_records", failures)
        save("quality", "quarantine", quarantine)
        if state == "BLOCKED":
            audit["status"] = "BLOCKED"
            audit["error_message"] = "Required quality gate failed; previous published Gold retained"
        else:
            for ds, frame in silver.items():
                save("silver", ds, frame.withColumn("pipeline_run_id", F.lit(run_id)))
            governed = {ds: spark.table(config.table("silver", ds)).filter(F.col("pipeline_run_id") == run_id).drop("pipeline_run_id") for ds in silver}
            gold = gold_spark(governed)
            for name, frame in gold.items():
                save("gold", name, frame.withColumn("pipeline_run_id", F.lit(run_id)))
            from olist.governance.native import apply_metadata
            apply_metadata(spark, config)
            # Single atomic pointer publication after all snapshot tables have been written.
            pointer = metadata_frame(spark, pd.DataFrame([{"run_id": run_id}]))
            pointer.write.format("delta").mode("overwrite").saveAsTable(config.table("quality", "published_run"))
            audit["status"] = "SUCCEEDED"
            audit["latest_source_event"] = str(governed["orders"].agg(F.max("order_purchase_timestamp")).first()[0])
    except Exception as exc:
        audit["status"] = "FAILED"
        audit["error_message"] = f"{type(exc).__name__}: {str(exc)[:500]}"
        raise
    finally:
        audit["ended_at"] = utcnow()
        audit["duration_seconds"] = (pd.Timestamp(audit["ended_at"]) - pd.Timestamp(started)).total_seconds()
        audit_write()
    if audit["status"] == "BLOCKED":
        raise RuntimeError(audit["error_message"])
    return audit


if __name__ == "__main__":
    from pyspark.sql import SparkSession
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default=Config.from_env().catalog)
    parser.add_argument("--prefix", default="olist")
    parser.add_argument("--volume", default="raw")
    parser.add_argument("--batch-end")
    args = parser.parse_args()
    print(execute(SparkSession.builder.getOrCreate(), Config(catalog=args.catalog, prefix=args.prefix, volume=args.volume), args.batch_end))
