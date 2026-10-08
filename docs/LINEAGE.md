# Lineage and traceability

The app exposes a simplified **declared** business path; it does not pretend this is a captured execution graph. Native Spark reads/writes use qualified UC tables, and the pipeline has now executed successfully in the live Databricks workspace. Native Catalog Explorer table/column lineage coverage has not yet been manually recorded; inspect Catalog Explorer → table → Lineage before making claims about captured native lineage.

Example: `olist_orders_dataset.csv.order_purchase_timestamp` → `/Volumes/<catalog>/<prefix>_bronze/<volume>/olist_orders_dataset.csv` → `<catalog>.<prefix>_bronze.orders.order_purchase_timestamp` (string plus run/file metadata) → required/parse/lifecycle controls → `<catalog>.<prefix>_silver.orders.order_purchase_timestamp` (timestamp) → `<catalog>.<prefix>_gold.fact_orders.purchase_date` (calendar date) → order-cohort selection → Total Orders / order trend → Executive Overview.

Financial path: item CSV `price` → Bronze order_items → numeric/nonnegative/key/FK controls and accepted-parent quarantine → Silver order_items → group by order_id before join → Gold fact_orders.item_gmv → delivered-order sum → Delivered Item GMV. Freight follows a separate path and is excluded from GMV. Payments are independently aggregated; they cannot multiply item prices. Reviews are resolved separately at one latest accepted review per order.

When a row fails multiple controls, `dq_failed_records` retains each `(run_id, dataset, source_record_id, rule_id)` violation and original payload. Bronze retains every selected source record; quarantine records explain exclusion from Silver. Parent exclusions create explicit dependent-child quarantine. Processing audit identifies the simulated cohort and publication outcome.

A source file SHA-256 manifest anchors traceability to exact landed bytes. Spark source-record IDs are run-local surrogates; correlate with run ID and original payload, not a fictitious stable row number. Native column-lineage coverage for custom quality routing, the Python metric service, and external Kaggle acquisition may be partial; document inspected coverage after deployment.
