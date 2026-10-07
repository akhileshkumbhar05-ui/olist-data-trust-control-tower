import argparse
from olist.config import Config
from olist.pipeline import run_local

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Use explicitly labeled synthetic data in isolated demo_data root")
    parser.add_argument("--batch-end", help="Exclusive purchase-date cutoff; cumulative simulation")
    args = parser.parse_args()
    config = Config.from_env()
    tables = None
    if args.demo:
        from pathlib import Path
        from tests.fixtures import demo_tables
        config = Config(Path("data/demo"), config.catalog, config.prefix, config.volume)
        tables = demo_tables()
        # A synthetic high-severity issue for routing demonstration (not actual data evidence).
        tables["order_items"].loc[1, "price"] = "-50"
    audit = run_local(config, args.batch_end, "DEMO / SYNTHETIC" if args.demo else "REAL OLIST", tables)
    print(audit)
    if audit["status"] != "SUCCEEDED":
        raise SystemExit(1)
