#!/usr/bin/env bash
set -euo pipefail
cd /workspace/olist-data-trust-control-tower
python -m venv /workspace/olist-venv
export PIP_CACHE_DIR=/workspace/olist-package-cache
/workspace/olist-venv/bin/python -m pip install -r requirements-lock.txt
/workspace/olist-venv/bin/python -m pip check
# Official CLI for schema validation and later OAuth-authorized deployment.
cli_base=/workspace/olist-tools
mkdir -p "$cli_base"
if [ ! -x "$cli_base/bin/databricks" ]; then
  curl -fL --retry 1 -o "$cli_base/cli.zip" https://github.com/databricks/cli/releases/download/v0.270.0/databricks_cli_0.270.0_linux_amd64.zip
  curl -fL --retry 1 -o "$cli_base/checksums.txt" https://github.com/databricks/cli/releases/download/v0.270.0/databricks_cli_0.270.0_SHA256SUMS
  /workspace/olist-venv/bin/python - <<'PY'
from pathlib import Path
import hashlib
import zipfile
base = Path('/workspace/olist-tools')
line = next(line for line in (base / 'checksums.txt').read_text().splitlines()
            if line.endswith('databricks_cli_0.270.0_linux_amd64.zip'))
if hashlib.sha256((base / 'cli.zip').read_bytes()).hexdigest() != line.split()[0]:
    raise RuntimeError('Official CLI archive checksum mismatch')
zipfile.ZipFile(base / 'cli.zip').extractall(base / 'bin')
PY
  chmod +x "$cli_base/bin/databricks"
fi
"$cli_base/bin/databricks" bundle schema > "$cli_base/bundle-schema.json"
PYTHONPATH=src:. /workspace/olist-venv/bin/python scripts/validate_config.py --schema "$cli_base/bundle-schema.json"
