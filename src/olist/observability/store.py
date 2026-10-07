"""Atomic local snapshots are a development harness; deployed persistence is Delta."""
from pathlib import Path
import json
import os
import pandas as pd


class LocalStore:
    def __init__(self, root: Path):
        self.root = root

    def write(self, layer, name, frame, run_id):
        destination = self.root / "runs" / run_id / layer / f"{name}.parquet"
        destination.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(destination, index=False)

    def read(self, layer, name, run_id=None):
        run_id = run_id or self.current()
        return pd.read_parquet(self.root / "runs" / run_id / layer / f"{name}.parquet")

    def current(self):
        return json.loads((self.root / "current.json").read_text())["run_id"]

    def publish(self, run_id):
        temporary = self.root / "current.json.tmp"
        temporary.write_text(json.dumps({"run_id": run_id}))
        os.replace(temporary, self.root / "current.json")

    def audit(self, record):
        dest = self.root / "audit" / f"{record['run_id']}.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        temporary = dest.with_suffix(".tmp")
        temporary.write_text(json.dumps(record, indent=2, default=str))
        os.replace(temporary, dest)

    def audits(self):
        return pd.DataFrame([json.loads(p.read_text()) for p in sorted((self.root / "audit").glob("*.json"))])
