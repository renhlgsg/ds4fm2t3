"""STEP 3 - run the DDL that provisions the star schema (dimensions + facts) under FDL_DATA.

Run:  python -m pipeline.provision_fdl
"""
from __future__ import annotations

from config import settings
from pipeline.db import log, run_sql_file, session, setup_logging


def provision_fdl(db_path=None) -> None:
    with session(db_path) as con:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.FDL}")
        run_sql_file(con, settings.SQL_DIR / "fdl" / "create_fdl_tables.sql", schema=settings.FDL)
        run_sql_file(con, settings.SQL_DIR / "fdl" / "seed_unknown_members.sql", schema=settings.FDL)
        rows = con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = ? "
            "AND table_name LIKE 'D\\_%' ESCAPE '\\' OR (table_schema = ? AND table_name LIKE 'F\\_%' ESCAPE '\\') "
            "ORDER BY 1", [settings.FDL, settings.FDL]).fetchall()
    log.info("FDL_DATA provisioned: %s", ", ".join(r[0] for r in rows))


if __name__ == "__main__":
    setup_logging()
    provision_fdl()
