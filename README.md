# E-Commerce Operations & Data Trust Control Tower

A Databricks-native historical e-commerce POC that connects operational KPIs to quality controls, quarantined records, governance metadata, metric definitions, processing history and lineage paths.

**Implemented and tested locally. Actual Kaggle files are now downloaded/profiled; live Databricks execution remains pending workspace URL, SQL warehouse and authentication.** The actual-data run and all ten app views are validated. A separate local rehearsal is prominently labeled DEMO / SYNTHETIC; it is not real Olist evidence. See [validation status](docs/VALIDATION.md) and [findings](docs/POC_FINDINGS.md).

## Quick start

Python 3.12 and Java 17+ (Java 21 validated). From the repository root:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
# Rehearsable synthetic vertical slice, isolated from real source outputs:
PYTHONPATH=src:. python scripts/run_local.py --demo
OLIST_DATA_ROOT=data/demo streamlit run app/app.py
# Meaningful unit, native Spark, service-boundary and UI tests:
pytest -q
```

For application-only use, install `requirements.txt`; Databricks Runtime supplies PySpark/Delta. `requirements-dev.txt` adds local Spark for tests. `requirements-lock.txt` records the validated full development package snapshot; it is not an extra application dependency list. UI pages render curated Gold/Quality outputs, never CSVs.

For the actual historical source (download and profile now validated in this environment):

```bash
export KAGGLEHUB_CACHE=/workspace/kaggle-cache
PYTHONPATH=src:. python scripts/acquire_profile.py
PYTHONPATH=src:. python scripts/run_local.py
# Cumulative purchase-date simulation, exclusive cutoff:
PYTHONPATH=src:. python scripts/run_local.py --batch-end 2018-02-01
OLIST_DATA_ROOT=data streamlit run app/app.py
```

KaggleHub is staging, not the governed raw store. The local harness retains exact originals and SHA-256 checksums under ignored `data/raw`. Deployment lands originals in a UC Volume and uses native Spark/Delta. Existing manifests are verified/reused, not blindly overwritten. No source files, generated data or credentials are committed.

## What is included

- Nine full-file verified source contracts, immutable landing and full-file profile generation.
- Versioned quality catalog: schema, completeness, keys, relationships, numeric/timestamp parsing, domains, temporal consistency and exploratory payment reconciliation.
- FAIL/QUARANTINE/WARN routing, original failure payloads, accepted-parent exclusion, deterministic readiness and explicit scoring.
- Grain-safe Silver and Gold models, canonical geography, independent child aggregates and latest-review selection.
- Centralized operational metric definitions and formulas, incident/quarantine drilldowns, data governance and processing history.
- Ten interactive views: Executive Overview, Operations, Data Quality, Incident Detail, Quarantine, Governance, Metric Dictionary, Lineage / Trust, Pipeline Health and About / Methodology.
- Native PySpark/Delta Serverless job and notebook entrypoint, Databricks Asset Bundle Job/App definitions, secure configuration examples, tests and a [five-minute demo rehearsal](docs/DEMO_SCRIPT.md).

## Structure

```text
app/                  Streamlit views, components and curated data service
src/olist/            Configuration, ingestion/profile, DQ, transformations,
                      governed metrics, governance and observability
pipelines/            Native Databricks PySpark/Delta job
scripts/              Acquire/profile, local pipeline, configuration validation
sql/                  Snapshot verification and UC grant examples
tests/                Isolated synthetic, native Spark, service and UI tests
docs/                 Architecture, dictionaries, policy, findings and runbook
databricks.yml        Bundle Job/App resources
app.yaml              Standalone Databricks App command/resource bindings
```

## Trust and limitations

The historical source is not live. Batch windows are cumulative purchase cohorts, not CDC or point-in-time historical views. Source grains/keys and dangerous cardinalities have been verified by full-file profiling; see DATA_PROFILE. GMV is not revenue, customer IDs have distinct meanings, child metrics cannot be summed across overlapping seller cohorts, and quality exceptions do not prove operational causality.

A critical failure or missing/erroring required check blocks new Gold publication. Prior metrics remain explicitly identified as previously published. Source snapshots and failures are retained for inspection. The quality score is equally weighted rule-record opportunity pass rate; repeated violations can count multiple times. Process readiness is a separate gate. Dependent-child quarantine is disclosed separately from direct rule scoring.

The app uses a shared service principal in Databricks and exposes source payloads to approved reviewers. Restrict its audience. Bounded SQL results fail loudly on truncation; production volumes require server-side aggregation/pagination. Deployment schema validation is not proof of live compatibility.

See [architecture](docs/ARCHITECTURE.md), [governance](docs/GOVERNANCE_MODEL.md), [source profile status](docs/DATA_PROFILE.md), [DQ catalog](docs/DATA_QUALITY_RULES.md), [metrics](docs/METRIC_DICTIONARY.md), [lineage](docs/LINEAGE.md), [deployment steps](docs/DEPLOYMENT.md), and [productionization](docs/PRODUCTIONIZATION.md).

The configured catalog default is `workspace`; `DATABRICKS_HOST` and `DATABRICKS_SQL_WAREHOUSE_ID` remain configurable. Serverless Jobs/notebooks do not require `DATABRICKS_CLUSTER_ID`. No Databricks resources were created in this cloud session. Configure workspace OAuth/service-principal access securely and supply nonsecret workspace/compute/warehouse identifiers before following the deployment runbook. Never paste secrets into chat or source files.
