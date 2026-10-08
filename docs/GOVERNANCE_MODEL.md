# Governance model

Catalog defaults to the user-confirmed `workspace`, configurable by `DATABRICKS_CATALOG` (legacy `OLIST_CATALOG` fallback) or bundle variable `catalog`. Four configurable schemas are `<prefix>_bronze`, `<prefix>_silver`, `<prefix>_gold`, `<prefix>_quality`; default prefix `olist`. Raw files live at `/Volumes/<catalog>/<prefix>_bronze/<volume>`; default volume `raw`.

| Asset | Logical responsibility | Classification | Retention / cadence |
|---|---|---|---|
| Kaggle originals / raw Volume | Source Data Steward | Public-origin data; restricted customer/text/location access in POC | Preserve original snapshot and checksums; download once |
| Bronze source snapshots | Data Engineering Owner | Restricted operational source copies | Cumulative simulated batches; run history retained for POC |
| Silver operational entities | Operations Data Product Owner | Internal, customer identities and locations restricted | Publish after record-level controls |
| Gold order/item facts | Operations Analytics Owner | Internal; customer identifiers restricted | Same snapshot publication as Silver |
| DQ rule catalog / history | Data Quality Steward | Internal controls; failed payloads restricted | Versioned rules; append per execution |
| Governed metrics | Operations Analytics Owner | Internal business reporting | Definitions reviewed with Operations before production |

Names are validated SQL identifiers. Table grain and candidate key are declared in the machine-readable catalog. Original source field names are preserved, including Olist spelling such as `product_name_lenght`. Bronze fields remain strings. Silver casts only accepted values. Delta history is keyed by run ID as well as business keys; a primary-key claim always applies **within one snapshot**, not across append history.

`src/olist/governance/native.py` applies table comments, important column comments, and `olist.logical_owner`, `olist.classification`, `olist.grain` properties. These are role metadata, not actual UC ownership transfers, enforced sensitivity tags or automatic grants. Live pipeline execution has occurred, but native lineage UI coverage has not yet been manually recorded; inspect Catalog Explorer before making captured-lineage claims. Designed lineage edges in the app are labeled as declared paths.

Create the catalog administratively. Give the pipeline principal USE CATALOG, USE SCHEMA, CREATE SCHEMA, CREATE TABLE and CREATE VOLUME where appropriate, plus READ VOLUME and WRITE VOLUME. It must own/manage generated tables sufficiently to append snapshots, update the audit/pointer, and apply comments/properties. Scope privileges to a POC catalog, not production.

Give the app principal USE CATALOG and USE SCHEMA on Gold/Quality and SELECT only on the application tables; no raw Volume or Bronze/Silver access is needed. Attach warehouse CAN_USE. All users of this POC app share its service-principal data access. Restrict app audience to approved Operations/DQ reviewers because incident/quarantine pages expose original source payloads, including optional review text. Production requires user-specific authorization, masking of free text and identifiers, and separate viewer/steward roles.

Proposed retention is POC-only. Production retention periods, privacy review, source license terms, ownership groups, freshness SLOs, enforced tags, and deletion policies require organizational decisions. Do not infer anonymity from a public dataset. Customer ZIP/city, persistent IDs and free-form reviews deserve restricted handling.
