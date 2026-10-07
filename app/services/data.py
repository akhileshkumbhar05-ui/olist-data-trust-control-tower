"""Curated data access. Databricks mode uses SDK OAuth and SQL statement execution."""
from datetime import date
import os
import time
import pandas as pd
from olist.config import Config, identifier
from olist.observability.store import LocalStore
from olist.metrics.definitions import calculate, segment_performance

TABLES = {"fact_orders": "gold", "fact_order_items": "gold", "metric_values": "gold",
          "dq_rules": "quality", "dq_rule_results": "quality", "dq_failed_records": "quality", "quarantine": "quality",
          "dq_dataset_scorecard": "quality", "dq_run_summary": "quality", "table_catalog": "quality",
          "metric_dictionary": "quality", "lineage_edges": "quality"}


class DataService:
    def __init__(self, config=None, client=None):
        self.config = config or Config.from_env()
        self.mode = os.getenv("OLIST_BACKEND", "local")
        if self.mode not in {"local", "databricks"}:
            raise ValueError("OLIST_BACKEND must be local or databricks")
        self.store = LocalStore(self.config.root)
        self.client = client
        self._cache = {}
        self.warehouse = os.getenv("DATABRICKS_SQL_WAREHOUSE_ID") or os.getenv("DATABRICKS_WAREHOUSE_ID")
        if self.mode == "databricks":
            if not self.warehouse:
                raise ValueError("Missing DATABRICKS_SQL_WAREHOUSE_ID (legacy DATABRICKS_WAREHOUSE_ID also supported)")
            if self.client is None:
                from databricks.sdk import WorkspaceClient
                self.client = WorkspaceClient()  # Databricks Apps injected service-principal OAuth

    def query(self, sql):
        from databricks.sdk.service.sql import StatementState, Disposition, Format
        response = self.client.statement_execution.execute_statement(
            warehouse_id=self.warehouse, statement=sql, wait_timeout="30s",
            disposition=Disposition.INLINE, format=Format.JSON_ARRAY, row_limit=200000)
        deadline = time.monotonic() + 180
        while response.status.state in {StatementState.PENDING, StatementState.RUNNING}:
            if time.monotonic() >= deadline:
                self.client.statement_execution.cancel_execution(response.statement_id)
                raise TimeoutError("SQL warehouse query exceeded 180 seconds")
            time.sleep(1)
            response = self.client.statement_execution.get_statement(response.statement_id)
        if response.status.state != StatementState.SUCCEEDED:
            raise RuntimeError("Databricks SQL statement failed; inspect workspace SQL history")
        if response.manifest.truncated:
            raise RuntimeError("Result truncated; narrow the selection or deploy server-side aggregates")
        columns = [c.name for c in response.manifest.schema.columns]
        rows = list(response.result.data_array or []) if response.result else []
        next_index = response.result.next_chunk_index if response.result else None
        while next_index is not None:
            chunk = self.client.statement_execution.get_statement_result_chunk_n(response.statement_id, next_index)
            rows.extend(chunk.data_array or [])
            next_index = chunk.next_chunk_index
        frame = pd.DataFrame(rows, columns=columns)
        for column in response.manifest.schema.columns:
            if column.type_name.value in {"INT", "LONG", "DOUBLE", "FLOAT", "DECIMAL", "SHORT", "BYTE"}:
                frame[column.name] = pd.to_numeric(frame[column.name], errors="raise")
            elif column.type_name.value == "BOOLEAN":
                frame[column.name] = frame[column.name].map({"true": True, "false": False, True: True, False: False})
        return frame

    def table(self, name, run_id=None):
        if name not in TABLES:
            raise ValueError(f"Unapproved application table: {name}")
        if self.mode == "local":
            return self.store.read(TABLES[name], name, run_id)
        if run_id is not None:
            import re
            if not re.fullmatch(r"[0-9a-f]{32}", run_id):
                raise ValueError("Invalid run identifier")
            # Run IDs are validated before interpolation; no arbitrary SQL input allowed.
            where = f"pipeline_run_id = '{run_id}'" if TABLES[name] == "gold" else f"run_id = '{run_id}'"
        elif TABLES[name] == "gold":
            where = f"pipeline_run_id = (SELECT run_id FROM {self.config.table('quality', 'published_run')})"
        else:
            where = f"run_id = (SELECT run_id FROM {self.config.table('quality', 'pipeline_run_audit')} ORDER BY started_at DESC LIMIT 1)"
        projection = {
            "fact_orders": "order_id, customer_unique_id, customer_state, purchase_date, order_status, is_delivered, is_cancelled, item_gmv, item_count, freight_value, review_score, delivery_eligible, is_late, delivery_days, delay_days",
            "fact_order_items": "order_id, order_item_id, seller_id, category, purchase_date, customer_state, order_status, delivery_eligible, is_late, delivery_days, delay_days, review_score, price"
        }.get(name, "*")
        key = (name, run_id)
        if key not in self._cache:
            self._cache[key] = self.query(f"SELECT {projection} FROM {self.config.table(TABLES[name], name)} WHERE {where}")
        return self._cache[key].copy()

    def audits(self):
        if self.mode == "local":
            return self.store.audits().sort_values("started_at", ascending=False)
        return self.query(f"SELECT * FROM {self.config.table('quality', 'pipeline_run_audit')} ORDER BY started_at DESC")

    def latest_quality(self, name):
        latest = self.audits().iloc[0].run_id
        return self.table(name, latest)

    def quality_history(self):
        if self.mode == "databricks":
            return self.query(f"SELECT * FROM {self.config.table('quality', 'dq_run_summary')} ORDER BY execution_timestamp")
        frames = []
        for run_id in self.audits().run_id:
            try:
                frames.append(self.table("dq_run_summary", run_id))
            except FileNotFoundError:
                continue
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def filtered_facts(self, start=None, end=None, state=None, status=None, seller=None, category=None):
        facts = self.table("fact_orders")
        items = self.table("fact_order_items")
        # Restrict each cohort at order grain. Seller/category scope selects whole associated orders.
        mask = pd.Series(True, index=facts.index)
        if start:
            mask &= facts.purchase_date.ge(str(start))
        if end:
            mask &= facts.purchase_date.le(str(end))
        if state:
            mask &= facts.customer_state.eq(state)
        if status:
            mask &= facts.order_status.eq(status)
        scoped_items = items
        if seller:
            scoped_items = scoped_items[scoped_items.seller_id.eq(seller)]
        if category:
            scoped_items = scoped_items[scoped_items.category.eq(category)]
        if seller or category:
            mask &= facts.order_id.isin(scoped_items.order_id)
        filtered = facts[mask].copy()
        return filtered, scoped_items[scoped_items.order_id.isin(filtered.order_id)].copy()

    def metrics(self, **filters):
        return calculate(self.filtered_facts(**filters)[0])

    def rankings(self, dimension, **filters):
        if dimension not in {"seller_id", "category", "customer_state"}:
            raise ValueError(dimension)
        return segment_performance(self.filtered_facts(**filters)[1], dimension)
