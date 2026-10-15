"""STEP 1b - ingest the 9 CSV files into the 9 RDL_DATA tables.

Full refresh per table (TRUNCATE + INSERT) inside one transaction per table, so a failed file
never leaves a half-loaded table. Each CSV is the complete extract, so re-running is idempotent.

Run:  python -m pipeline.ingest_rdl [--raw-dir C:\\path\\to\\csv]
"""
from __future__ import annotations

import argparse
from pathlib import Path

from config import settings
from pipeline.db import log, session, setup_logging


def _columns_of(con, schema: str, table: str) -> list[tuple[str, str]]:
    return con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position",
        [schema, table]).fetchall()


def ingest_table(con, tbl: settings.SourceTable, raw_dir: Path) -> int:
    csv_path = raw_dir / tbl.csv_file
    if not csv_path.exists():
        raise FileNotFoundError(f"Source file not found: {csv_path}")
    cols = _columns_of(con, settings.RDL, tbl.name)
    # Explicit column->type mapping: the DDL is the contract; a bad value fails loudly here.
    col_map = ", ".join(f"'{c}': '{t}'" for c, t in cols)
    ts = f", timestampformat='{tbl.timestamp_format}'" if tbl.timestamp_format else ""
    con.execute("BEGIN")
    try:
        con.execute(f"DELETE FROM {settings.RDL}.{tbl.name}")
        con.execute(
            f"INSERT INTO {settings.RDL}.{tbl.name} "
            f"SELECT * FROM read_csv(?, header=true, columns={{{col_map}}}{ts})",
            [str(csv_path)])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    return con.execute(f"SELECT count(*) FROM {settings.RDL}.{tbl.name}").fetchone()[0]


def ingest_all(db_path=None, raw_dir: Path | str | None = None) -> dict[str, int]:
    raw_dir = Path(raw_dir or settings.RAW_DIR)
    counts: dict[str, int] = {}
    with session(db_path) as con:
        for tbl in settings.SOURCE_TABLES:
            counts[tbl.name] = ingest_table(con, tbl, raw_dir)
            log.info("RDL %-30s <- %-42s %9d rows", tbl.name, tbl.csv_file, counts[tbl.name])
    return counts


def _csv_row_count(path: Path) -> int:
    """Independent check: rows in CSV (via DuckDB's own reader, header excluded)."""
    with session(":memory:") as con:  # type: ignore[arg-type]
        return con.execute("SELECT count(*) FROM read_csv(?, header=true, all_varchar=true)",
                           [str(path)]).fetchone()[0]


def reconcile(counts: dict[str, int], raw_dir: Path | str | None = None) -> None:
    """Fail if any table's loaded row count differs from the CSV row count."""
    raw_dir = Path(raw_dir or settings.RAW_DIR)
    bad = []
    for tbl in settings.SOURCE_TABLES:
        n = _csv_row_count(raw_dir / tbl.csv_file)
        if n != counts[tbl.name]:
            bad.append(f"{tbl.name}: csv={n} loaded={counts[tbl.name]}")
    if bad:
        raise RuntimeError("Ingestion reconciliation failed: " + "; ".join(bad))
    log.info("Ingestion reconciliation OK (CSV rows == RDL rows for all 9 tables)")


if __name__ == "__main__":
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", default=None)
    a = ap.parse_args()
    reconcile(ingest_all(raw_dir=a.raw_dir), a.raw_dir)
