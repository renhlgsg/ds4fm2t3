"""STEP 0 - create the EMPTY DuckDB database file and the three schemas.

Run:  python -m pipeline.create_database
Idempotent: re-running keeps existing data (schemas use IF NOT EXISTS).
Use --reset to delete the database file first.
"""
from __future__ import annotations

import argparse

from config import settings
from pipeline.db import log, session, setup_logging


def create_database(db_path=None, reset: bool = False) -> None:
    path = settings.DB_PATH if db_path is None else db_path
    path = __import__("pathlib").Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if reset and path.exists():
        path.unlink()
        log.warning("Deleted existing database %s", path)
    with session(path) as con:
        for schema in (settings.RDL, settings.SDL, settings.FDL):
            con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
        schemas = [r[0] for r in con.execute(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name IN ('RDL_DATA','SDL_DATA','FDL_DATA') ORDER BY 1").fetchall()]
    log.info("Database ready at %s with schemas %s", path, schemas)


if __name__ == "__main__":
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true", help="delete the database file first")
    create_database(reset=ap.parse_args().reset)
