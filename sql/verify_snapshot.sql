-- Substitute validated catalog/schema names and the selected run UUID.
-- Never aggregate append-only historical tables without selecting one snapshot.
SELECT run_id, status, records_received, accepted_records, quarantined_records,
       records_received = accepted_records + quarantined_records AS source_reconciles,
       error_message
FROM workspace.olist_quality.pipeline_run_audit
ORDER BY started_at DESC;

SELECT * FROM workspace.olist_quality.dq_run_summary
WHERE run_id = (SELECT run_id FROM workspace.olist_quality.published_run);

SELECT order_id, COUNT(*) AS duplicate_rows
FROM workspace.olist_gold.fact_orders
WHERE pipeline_run_id = (SELECT run_id FROM workspace.olist_quality.published_run)
GROUP BY order_id HAVING COUNT(*) > 1;

SELECT order_id, order_item_id, COUNT(*) AS duplicate_rows
FROM workspace.olist_gold.fact_order_items
WHERE pipeline_run_id = (SELECT run_id FROM workspace.olist_quality.published_run)
GROUP BY order_id, order_item_id HAVING COUNT(*) > 1;
