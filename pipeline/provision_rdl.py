"""STEP 1a - run the DDL that provisions the 9 raw tables under RDL_DATA.

Run:  python -m pipeline.provision_rdl
"""
from __future__ import annotations

from config import settings
from pipeline.db import log, run_sql_file, session, setup_logging


def provision_rdl(db_path=None) -> None:
    with session(db_path) as con:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.RDL}")
        run_sql_file(con, settings.SQL_DIR / "rdl" / "create_rdl_tables.sql", schema=settings.RDL)
        n = con.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = ?",
                        [settings.RDL]).fetchone()[0]
    log.info("RDL_DATA provisioned: %s tables", n)


if __name__ == "__main__":
    setup_logging()
    provision_rdl()
