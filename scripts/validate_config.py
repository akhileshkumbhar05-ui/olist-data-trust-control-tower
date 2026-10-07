"""Offline schema validation; does not imply live workspace deployment validation."""
from pathlib import Path
import argparse
import json
import yaml
from jsonschema import Draft202012Validator

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", required=True, help="Output of databricks bundle schema")
    args = parser.parse_args()
    schema = json.loads(Path(args.schema).read_text())
    config = yaml.safe_load(Path("databricks.yml").read_text())
    errors = sorted(Draft202012Validator(schema).iter_errors(config), key=lambda e: str(e.path))
    if errors:
        for err in errors:
            print(list(err.path), err.message)
        raise SystemExit(1)
    print("Bundle passes official CLI JSON schema. Authentication and workspace compatibility remain unvalidated.")
