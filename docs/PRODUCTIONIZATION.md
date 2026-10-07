# Productionization

Replace Kaggle with actual order management, payment, fulfillment and customer-experience systems. Confirm contract owners, key/grain semantics, accounting definitions and timestamp zones with business owners. Ingest CDC/event offsets with durable checkpoints, explicit late-arrival/reprocessing policies and idempotent Delta MERGE logic; chronological cumulative snapshots are a POC simplification.

Use Lakeflow Jobs/Declarative Pipelines where supported; retain custom rule history and quarantine metadata. Set separate dev/test/prod catalogs, identities and deployment targets. Size compute against source volume; move filtered metrics and rankings into governed SQL views/aggregates so application requests never collect full production facts.

Agree measurable processing/source freshness SLOs and observation windows. Alert on critical gates, failed runs, orphan growth, quarantine rates, schema drift and stale publication. Link incidents to responsible stewards; add acknowledgment, remediation, replay and resolution histories. Source-record IDs should become stable source primary key/version or offset identities. Track dependency exclusions as first-class quality incidents and monitor accepted metric coverage.

Use service principals and workload/OAuth authentication; keep credentials in secure Databricks/environment facilities. Enforce least privilege on UC and warehouse resources, customer/text masking, user-specific app authorization, sensitivity tags, audit-log retention and retention/deletion schedules. The POC app currently uses a shared app principal and must have a restricted audience.

CI should run isolated unit, native Spark, service-boundary and UI tests; validate bundle schema and authenticated compatibility in a disposable dev workspace. Add source contract regression fixtures, representative real-data reconciliation baselines, Delta concurrency/replay tests, performance budgets and schema evolution policies. Publish artifacts with verified dependencies. Require policy-controlled deployment to production and promotion of approved metric definitions.

Use UC native lineage and system tables to monitor actual executed paths and query history; supplement external acquisition and Python metric lineage where native coverage ends. Establish rollback/recovery procedures for partial snapshots and garbage collection for failed/old snapshots. The current single-writer pointer is suitable for a POC, not multi-job transactional coordination.
