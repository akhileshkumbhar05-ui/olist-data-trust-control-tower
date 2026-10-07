"""Native UC descriptions and role metadata; ownership/grants are administrator decisions."""
from olist.governance.catalog import table_catalog
from olist.ingestion.catalog import SOURCES


def sql_literal(text):
    return "'" + text.replace("'", "''") + "'"


def apply_metadata(spark, config):
    for row in table_catalog().itertuples(index=False):
        name = config.table(row.layer, row.table)
        if not spark.catalog.tableExists(name):
            continue
        comment = f"{row.description}. Grain: {row.grain}. Logical owner: {row.owner}. Historical Olist; cumulative simulated batches."
        spark.sql(f"COMMENT ON TABLE {name} IS {sql_literal(comment)}")
        spark.sql(f"ALTER TABLE {name} SET TBLPROPERTIES ('olist.logical_owner'={sql_literal(row.owner)}, 'olist.classification'={sql_literal(row.classification)}, 'olist.grain'={sql_literal(row.grain)})")
        columns = spark.table(name).columns
        for col in columns:
            detail = {
                "customer_id": "Order-specific customer identity; not persistent person identity",
                "customer_unique_id": "Persistent customer identity for repeat-customer cohort metrics",
                "source_record_id": "Run-local source row surrogate, distinct for duplicate raw rows; inspect with pipeline run ID",
                "order_id": "Source order identifier; unique within each order snapshot",
                "pipeline_run_id": "Snapshot/run identifier; required when querying append-only history",
                "purchase_date": "Source purchase calendar date; timestamp timezone unspecified",
                "is_late": "Delivered calendar day later than estimated calendar day; eligible deliveries only",
                "item_gmv": "Sum of accepted item prices per order in BRL; excludes freight, not accounting revenue",
            }.get(col, f"{col.replace('_', ' ')}; see data dictionary for source and interpretation")
            spark.sql(f"ALTER TABLE {name} ALTER COLUMN `{col}` COMMENT {sql_literal(detail)}")
