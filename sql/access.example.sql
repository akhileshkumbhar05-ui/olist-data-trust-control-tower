-- ADMINISTRATOR TEMPLATE ONLY. Replace principals/catalog explicitly; do not run as-is.
-- Restrict this app's audience because quarantine payloads can include source review text.
GRANT USE CATALOG ON CATALOG workspace TO `YOUR-APP-SERVICE-PRINCIPAL`;
GRANT USE SCHEMA ON SCHEMA workspace.olist_gold TO `YOUR-APP-SERVICE-PRINCIPAL`;
GRANT USE SCHEMA ON SCHEMA workspace.olist_quality TO `YOUR-APP-SERVICE-PRINCIPAL`;
GRANT SELECT ON SCHEMA workspace.olist_gold TO `YOUR-APP-SERVICE-PRINCIPAL`;
GRANT SELECT ON SCHEMA workspace.olist_quality TO `YOUR-APP-SERVICE-PRINCIPAL`;
-- No app grants on Bronze/Silver or raw Volume. Restrict app audience separately.
-- The pipeline needs UC create/write/manage rights in this isolated POC catalog,
-- plus access to serverless Jobs compute (or CAN_ATTACH_TO for optional classic compute). Consult GOVERNANCE_MODEL before granting.
