from dataclasses import dataclass
from pathlib import Path
import os
import re


def identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid SQL identifier: {value!r}")
    return value


@dataclass(frozen=True)
class Config:
    root: Path = Path("data")
    catalog: str = "workspace"
    prefix: str = "olist"
    volume: str = "raw"

    def __post_init__(self):
        for value in (self.catalog, self.prefix, self.volume):
            identifier(value)

    @classmethod
    def from_env(cls):
        return cls(Path(os.getenv("OLIST_DATA_ROOT", "data")),
                   os.getenv("DATABRICKS_CATALOG") or os.getenv("OLIST_CATALOG") or "workspace",
                   os.getenv("OLIST_SCHEMA_PREFIX", "olist"),
                   os.getenv("OLIST_VOLUME", "raw"))

    def schema(self, layer: str) -> str:
        if layer not in {"bronze", "silver", "gold", "quality"}:
            raise ValueError(layer)
        return f"{self.prefix}_{layer}"

    def table(self, layer: str, name: str) -> str:
        return f"{self.catalog}.{self.schema(layer)}.{identifier(name)}"

    @property
    def volume_path(self):
        return Path(f"/Volumes/{self.catalog}/{self.schema('bronze')}/{self.volume}")
