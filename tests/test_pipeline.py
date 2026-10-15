"""End-to-end tests (use the real CSVs in data/raw, in throw-away databases).

 1. test_initial_load_passes_dq                  - full pipeline, 0 DQ ERRORs
 2. test_rerun_is_idempotent                     - 2nd ELT run inserts/updates nothing
 3. test_incremental_equals_full_load            - partial load + incremental top-up == one full load
 4. test_incremental_picks_up_changed_order      - status change in source is propagated as an UPDATE
"""
from __future__ import annotations

import duckdb
import pytest

from config import settings
from pipeline import clean_sdl, create_database, dq_tests, elt_fdl, ingest_rdl, provision_fdl, provision_rdl

FACTS = ["F_ORDERS", "F_ORDER_ITEMS", "F_ORDER_PAYMENTS", "F_ORDER_REVIEWS"]


def _build_sdl(db):
    create_database.create_database(db, reset=True)
    provision_rdl.provision_rdl(db)
    ingest_rdl.ingest_all(db)
    clean_sdl.clean_all(db)
    provision_fdl.provision_fdl(db)


@pytest.fixture(scope="module")
def full_db(tmp_path_factory):
    db = tmp_path_factory.mktemp("full") / "full.duckdb"
    _build_sdl(db)
    elt_fdl.run_elt(db)
    return db


def test_initial_load_passes_dq(full_db):
    res = dq_tests.run_checks(full_db)
    assert [r for r in res if r["status"] == "FAIL"] == []
    assert len(res) > 100


def test_rerun_is_idempotent(full_db):
    res = elt_fdl.run_elt(full_db)
    assert all(ins == 0 and upd == 0 for ins, upd, _ in res.values()), res


def _fact_hashes(db):
    """Business content of every fact row, independent of surrogate keys."""
    con = duckdb.connect(str(db), read_only=True)
    out = {}
    out["F_ORDERS"] = con.execute(f"""SELECT md5(string_agg(CAST(t AS VARCHAR), '|' ORDER BY order_id)) FROM (
        SELECT order_id, order_status, purchase_ts, delivered_customer_ts, item_count, total_order_amount,
               total_payment_value, delivery_days, is_late FROM {settings.FDL}.F_ORDERS) t""").fetchone()[0]
    out["F_ORDER_ITEMS"] = con.execute(f"""SELECT md5(string_agg(CAST(t AS VARCHAR), '|' ORDER BY order_id, order_item_id)) FROM (
        SELECT order_id, order_item_id, order_status, price, freight_value, total_sale_amount
        FROM {settings.FDL}.F_ORDER_ITEMS) t""").fetchone()[0]
    out["F_ORDER_PAYMENTS"] = con.execute(f"""SELECT md5(string_agg(CAST(t AS VARCHAR), '|' ORDER BY order_id, payment_sequential)) FROM (
        SELECT order_id, payment_sequential, payment_value, payment_installments FROM {settings.FDL}.F_ORDER_PAYMENTS) t""").fetchone()[0]
    out["F_ORDER_REVIEWS"] = con.execute(f"""SELECT md5(string_agg(CAST(t AS VARCHAR), '|' ORDER BY review_id, order_id)) FROM (
        SELECT review_id, order_id, review_score, response_time_hours FROM {settings.FDL}.F_ORDER_REVIEWS) t""").fetchone()[0]
    out["D_CUSTOMER"] = con.execute(f"""SELECT md5(string_agg(CAST(t AS VARCHAR), '|' ORDER BY customer_unique_id)) FROM (
        SELECT customer_unique_id, total_orders, total_items, customer_lifetime_value, first_purchase_date, last_purchase_date
        FROM {settings.FDL}.D_CUSTOMER) t""").fetchone()[0]
    con.close()
    return out


def test_incremental_equals_full_load(full_db, tmp_path):
    """Load only the oldest ~80% of orders first, then top up with an incremental run."""
    db = tmp_path / "inc.duckdb"
    _build_sdl(db)
    con = duckdb.connect(str(db))
    S = settings.SDL
    con.execute(f"""CREATE TEMP TABLE late AS SELECT order_id FROM {S}.ORDERS
                    ORDER BY order_purchase_timestamp DESC LIMIT 20000""")
    # Hide the newest 20,000 orders (and children) from SDL -> simulates "yesterday's" extract
    backup = {t: con.execute(f"SELECT * FROM {S}.{t} WHERE order_id IN (SELECT order_id FROM late)").df()
              for t in ["ORDERS", "ORDER_ITEMS", "ORDER_PAYMENTS", "ORDER_REVIEWS"]}
    for t in backup:
        con.execute(f"DELETE FROM {S}.{t} WHERE order_id IN (SELECT order_id FROM late)")
    con.close()

    first = elt_fdl.run_elt(db)                                    # INITIAL on partial data
    assert first["F_ORDERS"][2] == 99441 - 20000

    _build_sdl_keep_fdl(db)                                        # "today's" full extract arrives
    second = elt_fdl.run_elt(db)                                   # INCREMENTAL top-up
    assert second["F_ORDERS"][0] == 20000                          # exactly the new orders inserted
    assert second["F_ORDERS"][2] == 99441

    assert _fact_hashes(db) == _fact_hashes(full_db)               # identical to a one-shot full load
    assert dq_tests.summarize(dq_tests.run_checks(db)) == 0


def _build_sdl_keep_fdl(db):
    """Refresh RDL+SDL from the CSVs without touching FDL (what the daily job does)."""
    provision_rdl.provision_rdl(db)
    ingest_rdl.ingest_all(db)
    clean_sdl.clean_all(db)


def test_incremental_picks_up_changed_order(tmp_path):
    db = tmp_path / "chg.duckdb"
    _build_sdl(db)
    elt_fdl.run_elt(db)
    con = duckdb.connect(str(db))
    oid = con.execute(f"SELECT order_id FROM {settings.SDL}.ORDERS WHERE order_status = 'shipped' LIMIT 1").fetchone()[0]
    con.execute(f"""UPDATE {settings.SDL}.ORDERS SET order_status = 'delivered',
                    order_delivered_customer_date = order_purchase_timestamp + INTERVAL 10 DAY WHERE order_id = ?""", [oid])
    con.close()
    res = elt_fdl.run_elt(db)
    assert res["F_ORDERS"][:2] == (0, 1)
    assert res["F_ORDER_ITEMS"][1] >= 1                            # status is carried on the item rows too
    con = duckdb.connect(str(db), read_only=True)
    row = con.execute(f"SELECT order_status, is_delivered, delivery_days FROM {settings.FDL}.F_ORDERS WHERE order_id = ?", [oid]).fetchone()
    assert row == ("delivered", True, 10.0)
