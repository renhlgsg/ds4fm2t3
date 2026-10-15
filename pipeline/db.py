"""Shared DuckDB helpers."""
from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path

import duckdb

from config import settings

log = logging.getLogger("ds4fm2t3")


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)-7s | %(message)s",
                        datefmt="%H:%M:%S")


def connect(db_path: Path | str | None = None, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    path = Path(db_path or settings.DB_PATH)
    return duckdb.connect(str(path), read_only=read_only)


@contextmanager
def session(db_path: Path | str | None = None, read_only: bool = False):
    con = connect(db_path, read_only)
    try:
        yield con
    finally:
        con.close()


def run_sql_file(con, sql_file: Path, **params: str) -> None:
    """Execute a .sql file after substituting {placeholders}."""
    text = Path(sql_file).read_text(encoding="utf-8")
    for key, val in params.items():
        text = text.replace("{" + key + "}", val)
    con.execute(text)
