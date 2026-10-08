# Deployment and access

## Target and current status

The known Unity Catalog catalog is `workspace`. The repository supports **Serverless Jobs** through the bundle and an existing Serverless notebook through `pipelines/serverless_notebook.py`; neither path requires a classic cluster ID.

The current POC has now been deployed manually in Databricks. The existing Serverless notebook path executed the real Olist pipeline successfully and created/used the governed UC Volume plus Bronze, Silver, Gold and Quality Delta assets. The Databricks App was created/deployed from Git, attached to an existing SQL warehouse, granted least-privilege Gold/Quality reads through its service principal, and smoke-tested across all ten views. Exact workspace/warehouse identifiers remain environment-specific and intentionally uncommitted. Bundle-based Job/App deployment and native lineage inspection remain separate validation items.

## Nonsecret configuration

| Name | Meaning / status |
|---|---|
| `DATABRICKS_HOST` | Workspace HTTPS base URL; known in the current deployed environment but intentionally not committed |
| `DATABRICKS_CATALOG` | `workspace` by default; may be overridden |
| `DATABRICKS_SQL_WAREHOUSE_ID` | Warehouse serving the app's curated queries; currently injected through the attached `sql-warehouse` App resource and intentionally not hardcoded |
| `DATABRICKS_CLUSTER_ID` | Optional placeholder for explicitly configuring classic compute later; unused by default serverless bundle |
| `DATABRICKS_SERVERLESS_ENVIRONMENT_VERSION` | Default `2`, configurable; choose a supported version in your workspace |
| `OLIST_SCHEMA_PREFIX` / `OLIST_VOLUME` | `olist` / `raw` by default |

Legacy `OLIST_CATALOG` and `DATABRICKS_WAREHOUSE_ID` remain fallbacks. Canonical names above take precedence when nonempty. Local development/tests do not require host, warehouse, cluster or workspace authentication. A populated `.env` is ignored; settings must be exported into the process (the app does not silently load `.env`).

## Where to find identifiers in the Databricks UI

1. **Workspace URL:** open your Databricks workspace in the browser. Copy only its base HTTPS origin from the address bar, such as `https://adb-….azuredatabricks.net` or your cloud's Databricks workspace hostname. Omit notebook path, `?o=…`, and other query parameters. Do not substitute the accounts-console URL.
2. **Catalog:** Catalog → Catalog Explorer → Catalogs → `workspace`. Confirm permission to create dedicated `olist_*` schemas there; an existing catalog does not imply those grants.
3. **SQL warehouse ID:** sidebar SQL → SQL Warehouses → select an existing usable warehouse → Connection details. Copy the warehouse ID, or the final ID in HTTP path `/sql/1.0/warehouses/<id>`. The warehouse detail URL also contains its identifier. If SQL Warehouses is absent, request the Databricks SQL entitlement from an administrator. If no warehouse exists, an authorized admin must create an appropriately sized one; it is separate from Serverless notebook compute.
4. **Cluster ID (optional only):** Compute → All-purpose compute → choose a classic cluster; its details URL contains `/compute/clusters/<id>` (older UI may use `/setting/clusters/<id>`). Serverless notebooks have no classic cluster ID. Leave `DATABRICKS_CLUSTER_ID` empty for this POC's serverless path.
5. **Serverless Jobs support:** Workflows / Jobs & Pipelines → create or inspect a Python script task → Compute should offer Serverless. Inspect its environment settings for an available version. Notebook serverless access alone does not prove job support.

## Minimum resources and permissions

| Principal / operation | Minimum access |
|---|---|
| Deployment identity | Workspace access, write to target workspace/Git folder path, create/manage the POC Job and App; access to Serverless Jobs compute, enabled Serverless Apps and applicable entitlements |
| Pipeline run identity | USE CATALOG on `workspace`; CREATE SCHEMA there (or admin precreation of the four schemas); USE SCHEMA plus CREATE TABLE/CREATE VOLUME in the target schemas; READ VOLUME/WRITE VOLUME for raw landing; ownership/manage rights on generated tables for audit MERGE, pointer overwrite and comments/properties |
| App service principal | CAN_USE on selected SQL warehouse; USE CATALOG on `workspace`; USE SCHEMA on `workspace.olist_gold` and `workspace.olist_quality`; SELECT on application tables in those schemas |
| App audience | Approved Operations/DQ reviewers; source incident payloads can expose review text and identifiers through a shared app principal |

No cluster permission is needed for serverless. A later classic-compute job would need CAN_ATTACH_TO on its chosen cluster and explicit job configuration; setting a cluster environment variable alone does not switch the bundle. Scope grants to dedicated schemas and generated POC objects; do not assume ownership of existing workspace assets. Databricks Apps warehouse attachment supplies CAN_USE but does not automatically grant UC table reads.

The job creates four schemas, one raw UC Volume, source Bronze/Silver Delta snapshots, Gold facts/dimensions, Quality history, an audit table and a publication pointer. It adds comments and logical governance properties. The catalog and SQL warehouse are existing resources; the bundle creates/manages the POC Job and App.

## Authentication

Use `databricks auth login --host "$DATABRICKS_HOST" --profile olist` and `databricks auth describe --profile olist` where interactive OAuth is supported. For unattended cloud execution, configure your organization's approved workload or service-principal OAuth authentication securely in environment settings. Never place tokens/client secrets in repository files or chat. Databricks Apps uses injected service-principal OAuth. No external token is needed inside a workspace Serverless notebook; execution uses its current identity and UC permissions.

## Bundle commands

Databricks CLI 0.270.0 or newer. The official checksum-verified v0.270.0 JSON schema validates the local bundle. The current live POC was deployed through the Serverless notebook plus manual App-from-Git path, so the bundle itself has not yet been authenticated/deployed end to end.

```bash
export DATABRICKS_HOST='https://YOUR-WORKSPACE-HOST'
export DATABRICKS_CATALOG='workspace'
export DATABRICKS_SQL_WAREHOUSE_ID='YOUR-WAREHOUSE-ID'
# Optional environment override; choose one supported by the workspace:
export DATABRICKS_SERVERLESS_ENVIRONMENT_VERSION='2'
# DATABRICKS_CLUSTER_ID is not needed.
databricks auth login --host "$DATABRICKS_HOST" --profile olist
python scripts/deploy.py validate --profile olist
python scripts/deploy.py deploy --profile olist
python scripts/deploy.py run --resource olist_pipeline --profile olist
python scripts/deploy.py run --resource control_tower --profile olist
```

`scripts/deploy.py` maps the nonsecret environment settings to native `BUNDLE_VAR_*` variables, preserving explicit Bundle overrides. It validates by default; it does not implicitly deploy. The complete bundle includes the SQL-backed App, so authenticated deployment requires its warehouse ID. Until then, notebook execution and all repository/local workflows remain available.

Equivalent direct CLI commands use `BUNDLE_VAR_workspace_host`, `BUNDLE_VAR_catalog`, `BUNDLE_VAR_warehouse_id`, and optionally `BUNDLE_VAR_serverless_environment_version`. Run cumulative simulation with `databricks bundle run -t dev --profile olist olist_pipeline --params batch_end=2018-02-01`. The default cutoff is empty, meaning full historical snapshot.

## Existing Serverless notebook path

Import/open `pipelines/serverless_notebook.py` in a Databricks Git folder containing this repository. Configure its notebook environment with the pinned libraries listed in `requirements-pipeline.txt` once; no per-run ad-hoc installation is part of the pipeline. Set `repository_root` widget to the actual Git folder checkout root. Catalog defaults to `workspace`; schema prefix, Volume and purchase cutoff are widgets. Execute the notebook. This path needs no external workspace credential, SQL warehouse or classic cluster; it needs the pipeline UC permissions and Kaggle egress. Install the declared requirements file using the workspace-supported notebook environment workflow if libraries are absent.

The native job avoids DataFrame caching and classic `SparkContext` APIs to accommodate Serverless/Spark Connect restrictions. Bronze writes materialize source row surrogates before DQ reads; audit updates use SQL MERGE. This Serverless notebook path has now executed successfully in the current workspace against the real Olist source.

## App and readiness checks

Bundle-resolved App configuration and standalone `app.yaml` default to `workspace`/`olist`; manual deployment to other names must update the nonsecret App configuration. `valueFrom: sql-warehouse` binds `DATABRICKS_SQL_WAREHOUSE_ID`. Grant UC reads to the app's generated service principal, inspect deployment logs, and exercise all ten pages.

Kaggle destinations are `www.kaggle.com`, `storage.googleapis.com`, `www.kaggleusercontent.com`; allow them in Databricks serverless egress policy as needed. A public-source request should be tested before asking for Kaggle credentials. TLS and checksums remain enabled.

After execution, inspect pipeline audit, quality summary, violations and quarantine, then `published_run`; filter every fact query by that run. Received must reconcile to accepted plus distinct quarantine; fact grains and accepted Silver counts must reconcile; critical failures must preserve the old publication pointer. Inspect native UC lineage/comments and a representative app request. A port/health check alone does not establish functional correctness.
