# Versioned data-quality rules

Runtime catalog: `src/olist/quality/rules.py`. All rules default active, version 1, logical owner Data Quality Steward. Rule IDs are stable within this version. Deactivate rules explicitly; inactive rules do not execute or enter the score. A required skipped/missing/erroring check blocks readiness. ERROR evaluations contribute zero evaluated opportunities, preserve affected records, and block publication.

READY = all required executed gates passed. WARNING = noncritical violations or dependent-parent exclusions. BLOCKED = CRITICAL violation, FAIL action, or unavailable/erroring required controls. QUARANTINE excludes all ambiguous duplicate rows; WARN retains records and exposes their payloads. Parent exclusion can trigger downstream quarantine even when a raw FK originally existed.

Score = 100 × (1 − sum(records_failed) / sum(records_evaluated)) over active executed checks. No severity weights. Schema checks use one table-level opportunity; row checks use source rows. An empty denominator yields zero, never a fabricated perfect score. Distinct rejected records are a separate count. Dependent-parent exclusions are not included in the direct-rule score and are explicitly surfaced in scorecards, failures and audit counts.

Payments versus item price + freight and lifecycle sequencing use WARN because accounting/event semantics are not confirmed. Lateness is an operational outcome, not a quality failure. Processing freshness comes from audit timestamps and source-event coverage; there is no live Kaggle source SLA.

| Rule ID | Dataset | Rule / rationale | Type | Severity | Action |
|---|---|---|---|---|---|
| orders.schema | orders | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| orders.required_key | orders | Candidate keys are present | COMPLETENESS | CRITICAL | QUARANTINE |
| orders.unique_key | orders | Candidate key is unique | UNIQUENESS | CRITICAL | QUARANTINE |
| orders.parse_order_purchase_timestamp | orders | order_purchase_timestamp parses as timestamp | SCHEMA | HIGH | QUARANTINE |
| orders.parse_order_approved_at | orders | order_approved_at parses as timestamp | SCHEMA | HIGH | QUARANTINE |
| orders.parse_order_delivered_carrier_date | orders | order_delivered_carrier_date parses as timestamp | SCHEMA | HIGH | QUARANTINE |
| orders.parse_order_delivered_customer_date | orders | order_delivered_customer_date parses as timestamp | SCHEMA | HIGH | QUARANTINE |
| orders.parse_order_estimated_delivery_date | orders | order_estimated_delivery_date parses as timestamp | SCHEMA | HIGH | QUARANTINE |
| customers.schema | customers | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| customers.required_key | customers | Candidate keys are present | COMPLETENESS | CRITICAL | QUARANTINE |
| customers.unique_key | customers | Candidate key is unique | UNIQUENESS | CRITICAL | QUARANTINE |
| order_items.schema | order_items | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| order_items.required_key | order_items | Candidate keys are present | COMPLETENESS | CRITICAL | QUARANTINE |
| order_items.unique_key | order_items | Candidate key is unique | UNIQUENESS | CRITICAL | QUARANTINE |
| order_items.parse_order_item_id | order_items | order_item_id parses as number | SCHEMA | HIGH | QUARANTINE |
| order_items.parse_price | order_items | price parses as number | SCHEMA | HIGH | QUARANTINE |
| order_items.parse_freight_value | order_items | freight_value parses as number | SCHEMA | HIGH | QUARANTINE |
| order_items.parse_shipping_limit_date | order_items | shipping_limit_date parses as timestamp | SCHEMA | HIGH | QUARANTINE |
| payments.schema | payments | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| payments.required_key | payments | Candidate keys are present | COMPLETENESS | CRITICAL | QUARANTINE |
| payments.unique_key | payments | Candidate key is unique | UNIQUENESS | CRITICAL | QUARANTINE |
| payments.parse_payment_sequential | payments | payment_sequential parses as number | SCHEMA | HIGH | QUARANTINE |
| payments.parse_payment_installments | payments | payment_installments parses as number | SCHEMA | HIGH | QUARANTINE |
| payments.parse_payment_value | payments | payment_value parses as number | SCHEMA | HIGH | QUARANTINE |
| reviews.schema | reviews | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| reviews.required_key | reviews | Candidate keys are present | COMPLETENESS | CRITICAL | QUARANTINE |
| reviews.unique_key | reviews | Candidate key is unique | UNIQUENESS | CRITICAL | QUARANTINE |
| reviews.parse_review_score | reviews | review_score parses as number | SCHEMA | HIGH | QUARANTINE |
| reviews.parse_review_creation_date | reviews | review_creation_date parses as timestamp | SCHEMA | HIGH | QUARANTINE |
| reviews.parse_review_answer_timestamp | reviews | review_answer_timestamp parses as timestamp | SCHEMA | HIGH | QUARANTINE |
| products.schema | products | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| products.required_key | products | Candidate keys are present | COMPLETENESS | CRITICAL | QUARANTINE |
| products.unique_key | products | Candidate key is unique | UNIQUENESS | CRITICAL | QUARANTINE |
| products.parse_product_name_lenght | products | product_name_lenght parses as number | SCHEMA | HIGH | QUARANTINE |
| products.parse_product_description_lenght | products | product_description_lenght parses as number | SCHEMA | HIGH | QUARANTINE |
| products.parse_product_photos_qty | products | product_photos_qty parses as number | SCHEMA | HIGH | QUARANTINE |
| products.parse_product_weight_g | products | product_weight_g parses as number | SCHEMA | HIGH | QUARANTINE |
| products.parse_product_length_cm | products | product_length_cm parses as number | SCHEMA | HIGH | QUARANTINE |
| products.parse_product_height_cm | products | product_height_cm parses as number | SCHEMA | HIGH | QUARANTINE |
| products.parse_product_width_cm | products | product_width_cm parses as number | SCHEMA | HIGH | QUARANTINE |
| sellers.schema | sellers | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| sellers.required_key | sellers | Candidate keys are present | COMPLETENESS | CRITICAL | QUARANTINE |
| sellers.unique_key | sellers | Candidate key is unique | UNIQUENESS | CRITICAL | QUARANTINE |
| geolocation.schema | geolocation | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| geolocation.parse_geolocation_lat | geolocation | geolocation_lat parses as number | SCHEMA | HIGH | QUARANTINE |
| geolocation.parse_geolocation_lng | geolocation | geolocation_lng parses as number | SCHEMA | HIGH | QUARANTINE |
| translation.schema | translation | Source columns match contract | SCHEMA | CRITICAL | FAIL |
| translation.required_key | translation | Candidate keys are present | COMPLETENESS | CRITICAL | QUARANTINE |
| translation.unique_key | translation | Candidate key is unique | UNIQUENESS | CRITICAL | QUARANTINE |
| orders.required_customer_id | orders | customer_id is present | COMPLETENESS | HIGH | QUARANTINE |
| orders.fk_customer_id | orders | customer_id exists in customers | REFERENTIAL | HIGH | QUARANTINE |
| order_items.required_order_id | order_items | order_id is present | COMPLETENESS | HIGH | QUARANTINE |
| order_items.fk_order_id | order_items | order_id exists in orders | REFERENTIAL | HIGH | QUARANTINE |
| order_items.required_product_id | order_items | product_id is present | COMPLETENESS | HIGH | QUARANTINE |
| order_items.fk_product_id | order_items | product_id exists in products | REFERENTIAL | HIGH | QUARANTINE |
| order_items.required_seller_id | order_items | seller_id is present | COMPLETENESS | HIGH | QUARANTINE |
| order_items.fk_seller_id | order_items | seller_id exists in sellers | REFERENTIAL | HIGH | QUARANTINE |
| payments.required_order_id | payments | order_id is present | COMPLETENESS | HIGH | QUARANTINE |
| payments.fk_order_id | payments | order_id exists in orders | REFERENTIAL | HIGH | QUARANTINE |
| reviews.required_order_id | reviews | order_id is present | COMPLETENESS | HIGH | QUARANTINE |
| reviews.fk_order_id | reviews | order_id exists in orders | REFERENTIAL | HIGH | QUARANTINE |
| products.fk_product_category_name | products | product_category_name exists in translation | REFERENTIAL | MEDIUM | WARN |
| orders.required_events | orders | Purchase and estimate are present | COMPLETENESS | HIGH | QUARANTINE |
| customers.persistent_id | customers | Persistent customer identity is present | COMPLETENESS | HIGH | QUARANTINE |
| orders.status | orders | Recognized order status | DOMAIN | HIGH | QUARANTINE |
| payments.type | payments | Recognized payment type | DOMAIN | MEDIUM | WARN |
| reviews.score | reviews | Review score from 1 to 5 | DOMAIN | HIGH | QUARANTINE |
| order_items.nonnegative_price | order_items | price is nonnegative | DOMAIN | HIGH | QUARANTINE |
| order_items.nonnegative_freight_value | order_items | freight_value is nonnegative | DOMAIN | HIGH | QUARANTINE |
| payments.nonnegative_payment_value | payments | payment_value is nonnegative | DOMAIN | HIGH | QUARANTINE |
| payments.nonnegative_payment_installments | payments | payment_installments is nonnegative | DOMAIN | HIGH | QUARANTINE |
| products.nonnegative_product_name_lenght | products | product_name_lenght is nonnegative | DOMAIN | HIGH | QUARANTINE |
| products.nonnegative_product_description_lenght | products | product_description_lenght is nonnegative | DOMAIN | HIGH | QUARANTINE |
| products.nonnegative_product_photos_qty | products | product_photos_qty is nonnegative | DOMAIN | HIGH | QUARANTINE |
| products.nonnegative_product_weight_g | products | product_weight_g is nonnegative | DOMAIN | HIGH | QUARANTINE |
| products.nonnegative_product_length_cm | products | product_length_cm is nonnegative | DOMAIN | HIGH | QUARANTINE |
| products.nonnegative_product_height_cm | products | product_height_cm is nonnegative | DOMAIN | HIGH | QUARANTINE |
| products.nonnegative_product_width_cm | products | product_width_cm is nonnegative | DOMAIN | HIGH | QUARANTINE |
| customers.state | customers | Valid Brazilian state | DOMAIN | MEDIUM | WARN |
| sellers.state | sellers | Valid Brazilian state | DOMAIN | MEDIUM | WARN |
| geolocation.state | geolocation | Valid Brazilian state | DOMAIN | MEDIUM | WARN |
| geolocation.geolocation_lat | geolocation | Physical coordinate bounds | DOMAIN | HIGH | QUARANTINE |
| geolocation.geolocation_lng | geolocation | Physical coordinate bounds | DOMAIN | HIGH | QUARANTINE |
| geolocation.zip | geolocation | ZIP prefix is present | COMPLETENESS | HIGH | QUARANTINE |
| products.category | products | Category is populated | COMPLETENESS | MEDIUM | WARN |
| orders.delivered_time | orders | Delivered orders have delivery event | BUSINESS | HIGH | QUARANTINE |
| orders.lifecycle | orders | Check adjacent known events only for delivered orders; do not infer causal impact or require events for canceled orders. | TEMPORAL | MEDIUM | WARN |
| orders.payment_reconciliation | orders | Compare payments to item price plus freight when both are present. Accounting semantics unconfirmed; discrepancy is a warning, not evidence of incorrect revenue. | BUSINESS | MEDIUM | WARN |
