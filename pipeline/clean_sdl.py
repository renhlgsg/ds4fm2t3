"""STEP 2 - clean RDL_DATA -> SDL_DATA.

Rules (from the contract, applied in this order for every table):
  1. Delete rows where any primary-key column is missing (NULL, or blank for strings).
  2. Numeric column missing           -> 0
  3. String column missing / blank    -> 'Unspecified'
  4. Duplicate rows (all columns)     -> keep one  (SELECT DISTINCT after steps 2-3)
  Safety net (implementation recommendation, not in contract): if two *different* rows still share
  a primary key after step 4, keep one deterministically and log it, so the PK can be enforced.
TIMESTAMP columns are NOT numeric or string, so NULL timestamps are left NULL (e.g. an order
that is not yet delivered has no delivery date). This interpretation is documented in docs/.

SDL tables are rebuilt from RDL on every run (cheap, deterministic, idempotent).

Run:  python -m pipeline.clean_sdl
"""
from __future__ import annotations

from config import settings
from pipeline.db import log, run_sql_file, session, setup_logging

NUMERIC_TYPES = ("INTEGER", "BIGINT", "SMALLINT", "TINYINT", "DOUBLE", "FLOAT", "REAL", "DECIMAL", "HUGEINT")


def _is_numeric(dtype: str) -> bool:
    return dtype.upper().startswith(NUMERIC_TYPES)


def provision_sdl(con) -> None:
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {settings.SDL}")
    run_sql_file(con, settings.SQL_DIR / "sdl" / "create_sdl_tables.sql", schema=settings.SDL)


def build_clean_select(con, tbl: settings.SourceTable) -> tuple[str, list[str]]:
    cols = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position",
        [settings.RDL, tbl.name]).fetchall()
    exprs, pk_filters = [], []
    for name, dtype in cols:
        if _is_numeric(dtype):
            exprs.append(f"COALESCE({name}, 0) AS {name}")
            if name in tbl.pk:
                pk_filters.append(f"{name} IS NOT NULL")
        elif dtype.upper().startswith("VARCHAR"):
            exprs.append(f"COALESCE(NULLIF(TRIM({name}), ''), 'Unspecified') AS {name}")
            if name in tbl.pk:
                pk_filters.append(f"NULLIF(TRIM({name}), '') IS NOT NULL")
        else:  # TIMESTAMP etc. -> untouched
            exprs.append(name)
            if name in tbl.pk:
                pk_filters.append(f"{name} IS NOT NULL")
    where = " AND ".join(pk_filters) or "TRUE"
    sql = (f"SELECT DISTINCT {', '.join(exprs)} FROM {settings.RDL}.{tbl.name} WHERE {where}")
    return sql, [c for c, _ in cols]


def clean_table(con, tbl: settings.SourceTable) -> dict[str, int]:
    raw_n = con.execute(f"SELECT count(*) FROM {settings.RDL}.{tbl.name}").fetchone()[0]
    pk_filters = " AND ".join(f"NULLIF(TRIM(CAST({c} AS VARCHAR)), '') IS NOT NULL" for c in tbl.pk)
    missing_pk = con.execute(
        f"SELECT count(*) FROM {settings.RDL}.{tbl.name} WHERE NOT ({pk_filters})").fetchone()[0]
    select_sql, cols = build_clean_select(con, tbl)
    distinct_n = con.execute(f"SELECT count(*) FROM ({select_sql})").fetchone()[0]
    pk = ", ".join(tbl.pk)
    con.execute("BEGIN")
    try:
        con.execute(f"DELETE FROM {settings.SDL}.{tbl.name}")
        con.execute(
            f"INSERT INTO {settings.SDL}.{tbl.name} ({', '.join(cols)}) "
            f"SELECT {', '.join(cols)} FROM ({select_sql}) "
            f"QUALIFY row_number() OVER (PARTITION BY {pk} ORDER BY {', '.join(cols)}) = 1")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    clean_n = con.execute(f"SELECT count(*) FROM {settings.SDL}.{tbl.name}").fetchone()[0]
    return {"raw": raw_n, "missing_pk_deleted": missing_pk,
            "duplicates_deleted": raw_n - missing_pk - (distinct_n if missing_pk == 0 else
                                   con.execute(f"SELECT count(*) FROM ({select_sql})").fetchone()[0]),
            "pk_conflicts_resolved": distinct_n - clean_n, "clean": clean_n}


def clean_all(db_path=None) -> dict[str, dict[str, int]]:
    out = {}
    with session(db_path) as con:
        provision_sdl(con)
        for tbl in settings.SOURCE_TABLES:
            out[tbl.name] = clean_table(con, tbl)
            s = out[tbl.name]
            log.info("SDL %-30s raw=%9d  missingPK=%d  dups=%d  pkConflicts=%d  clean=%9d",
                     tbl.name, s["raw"], s["missing_pk_deleted"], s["duplicates_deleted"],
                     s["pk_conflicts_resolved"], s["clean"])
    return out


if __name__ == "__main__":
    setup_logging()
    clean_all()
