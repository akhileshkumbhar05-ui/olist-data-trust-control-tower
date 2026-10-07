"""Map nonsecret environment configuration to Bundle variables; no deployment by default."""
import argparse
import os
from pathlib import Path
import subprocess

BINDINGS = {
    "DATABRICKS_HOST": "workspace_host",
    "DATABRICKS_CATALOG": "catalog",
    "DATABRICKS_SQL_WAREHOUSE_ID": "warehouse_id",
    "DATABRICKS_SERVERLESS_ENVIRONMENT_VERSION": "serverless_environment_version",
    "OLIST_SCHEMA_PREFIX": "schema_prefix",
    "OLIST_VOLUME": "raw_volume",
}


def bundle_environment(environment):
    result = dict(environment)
    for source, target in BINDINGS.items():
        if result.get(source):
            result.setdefault(f"BUNDLE_VAR_{target}", result[source])
    result.setdefault("BUNDLE_VAR_catalog", "workspace")
    missing = [key for key in ("workspace_host", "warehouse_id") if not result.get(f"BUNDLE_VAR_{key}")]
    if missing:
        raise ValueError("Live bundle operations need nonsecret identifiers: " + ", ".join(missing)
                         + ". See docs/DEPLOYMENT.md. Local development requires neither.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("validate", "deploy", "run"), nargs="?", default="validate")
    parser.add_argument("--resource", choices=("olist_pipeline", "control_tower"))
    parser.add_argument("--profile", default="olist")
    parser.add_argument("--cli", default="databricks")
    args = parser.parse_args()
    try:
        environment = bundle_environment(os.environ)
    except ValueError as exc:
        parser.error(str(exc))
    command = [args.cli, "bundle", args.action, "-t", "dev", "--profile", args.profile]
    if args.action == "run":
        if not args.resource:
            parser.error("--resource is required for run")
        command.append(args.resource)
    raise SystemExit(subprocess.run(command, env=environment, cwd=Path(__file__).resolve().parents[1]).returncode)
