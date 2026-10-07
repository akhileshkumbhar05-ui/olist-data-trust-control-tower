from pathlib import Path
from olist.config import Config
from olist.ingestion.acquire import land, read_sources
from olist.ingestion.profile import profile

if __name__ == "__main__":
    config = Config.from_env()
    manifest = land(config.root / "raw")
    report = profile(read_sources(config.root / "raw"), Path("docs"))
    print({name: value["rows"] for name, value in report["datasets"].items()})
    print(report["cardinality_findings"])
