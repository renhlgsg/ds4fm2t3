"""STEP 4 - ELT: SDL_DATA -> FDL_DATA (dimensions first, then facts).

One generic, metadata-driven loader handles both the INITIAL load and every INCREMENTAL load:

  1. The transformation SQL (sql/elt/<target>.sql) is materialised into a TEMP staging table.
  2. A row_hash (md5 of every column) is computed for each staged row.
  3. UPDATE  target rows whose natural key exists but whose row_hash differs   (changed rows)
  4. INSERT  staged rows whose natural key does not yet exist in the target     (new rows)
  Rows already identical are untouched -> a re-run with no source change inserts/updates 0 rows.

Initial vs incremental is detected automatically (target holds only the -1 'Unknown' member => INITIAL).
Everything for one target runs in one transaction. Outcomes are written to FDL_DATA.ETL_RUN_LOG.
Deletes in the source are not propagated (facts are retained); see docs for the rationale.

Run:  python -m pipeline.elt_fdl
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from config import settings
from pipeline.db import log, session, setup_logging


@dataclass(frozen=True)
class Job:
    target: str
    natural_key: tuple[str, ...]
    sql_file: str
    surrogate_key: str | None = None   # filled automatically by the column DEFAULT (sequence)


# Order matters: dimensions before the facts that look them up.
JOBS: list[Job] = [
    Job("D_DATE",         ("date_key",),               "d_date.sql"),
    Job("D_GEOGRAPHY",    ("zip_code_prefix",),        "d_geography.sql", "geography_key"),
    Job("D_PAYMENT_TYPE", ("payment_type_code",),      "d_payment_type.sql", "payment_type_key"),
    Job("D_PRODUCT",      ("product_id",),             "d_product.sql", "product_key"),
    Job("D_SELLER",       ("seller_id",),              "d_seller.sql", "seller_key"),
    Job("D_CUSTOMER",     ("customer_unique_id",),     "d_customer.sql", "customer_key"),
    Job("F_ORDERS",         ("order_id",),                      "f_orders.sql"),
    Job("F_ORDER_ITEMS",    ("order_id", "order_item_id"),      "f_order_items.sql"),
    Job("F_ORDER_PAYMENTS", ("order_id", "payment_sequential"), "f_order_payments.sql"),
    Job("F_ORDER_REVIEWS",  ("review_id", "order_id"),          "f_order_reviews.sql"),
]


def _count(con, table: str) -> int:
    return con.execute(f"SELECT count(*) FROM {settings.FDL}.{table}").fetchone()[0]


def _is_dim(job: Job) -> bool:
    return job.target.startswith("D_")


def load_target(con, job: Job, run_id: str) -> tuple[int, int, int]:
    """Load one target. Returns (inserted, updated, total_rows_after)."""
    sql = (settings.SQL_DIR / "elt" / job.sql_file).read_text(encoding="utf-8")
    sql = sql.replace("{sdl}", settings.SDL).replace("{fdl}", settings.FDL)
    fq = f"{settings.FDL}.{job.target}"
    started = datetime.now()

    # INITIAL when the target holds nothing but the seeded -1 'Unknown' member (dimensions) / nothing (facts)
    seeded = 1 if _is_dim(job) else 0
    run_type = "INITIAL" if _count(con, job.target) <= seeded else "INCREMENTAL"

    con.execute("BEGIN")
    try:
        con.execute(f"CREATE OR REPLACE TEMP TABLE stg_raw AS {sql}")
        cols = [r[0] for r in con.execute("DESCRIBE stg_raw").fetchall()]
        hash_expr = "md5(concat_ws('|', " + ", ".join(
            f"COALESCE(CAST({c} AS VARCHAR), '~')" for c in cols) + "))"
        con.execute(f"CREATE OR REPLACE TEMP TABLE stg AS SELECT *, {hash_expr} AS row_hash FROM stg_raw")

        join_on = " AND ".join(f"t.{k} = s.{k}" for k in job.natural_key)
        non_key = [c for c in cols if c not in job.natural_key] + ["row_hash"]

        updated = con.execute(
            f"SELECT count(*) FROM stg s JOIN {fq} t ON {join_on} WHERE t.row_hash <> s.row_hash").fetchone()[0]
        if updated:
            set_clause = ", ".join(f"{c} = s.{c}" for c in non_key) + ", dw_updated_at = current_timestamp" \
                if job.target != "D_DATE" else ", ".join(f"{c} = s.{c}" for c in non_key)
            con.execute(f"UPDATE {fq} AS t SET {set_clause} FROM stg s WHERE {join_on} AND t.row_hash <> s.row_hash")

        before = _count(con, job.target)
        ins_cols = ", ".join(cols + ["row_hash"])
        con.execute(
            f"INSERT INTO {fq} ({ins_cols}) SELECT {ins_cols} FROM stg s "
            f"WHERE NOT EXISTS (SELECT 1 FROM {fq} t WHERE {join_on})")
        total = _count(con, job.target)
        inserted = total - before

        con.execute(f"INSERT INTO {settings.FDL}.ETL_RUN_LOG VALUES (?,?,?,?,?,?,?,?)",
                    [run_id, job.target, run_type, inserted, updated, total, started, datetime.now()])
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
    log.info("FDL %-17s %-11s inserted=%8d updated=%6d total=%8d", job.target, run_type, inserted, updated, total)
    return inserted, updated, total


def run_elt(db_path=None, jobs: list[Job] | None = None) -> dict[str, tuple[int, int, int]]:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:6]
    results = {}
    with session(db_path) as con:
        for job in jobs or JOBS:
            results[job.target] = load_target(con, job, run_id)
    log.info("ELT run %s complete", run_id)
    return results


if __name__ == "__main__":
    setup_logging()
    run_elt()
