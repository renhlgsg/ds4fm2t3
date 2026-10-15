"""Central configuration for project ds4fm2t3.

Every path / schema name / table definition lives here so no other module hard-codes them.
Override with environment variables (useful on the Windows deployment machine).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]          # ...\ds4fm2t3
RAW_DIR = Path(os.getenv("DS4FM2T3_RAW_DIR", PROJECT_ROOT / "data" / "raw"))
DB_PATH = Path(os.getenv("DS4FM2T3_DB_PATH", PROJECT_ROOT / "data" / "warehouse" / "ds4fm2t3.duckdb"))
SQL_DIR = PROJECT_ROOT / "sql"

# Schema names are fixed by the project contract.
RDL = "RDL_DATA"   # raw, populated by ingestion
SDL = "SDL_DATA"   # cleaned
FDL = "FDL_DATA"   # star schema (dimensions + facts)

# Dagster schedule: 04:00 daily. Timezone is NOT specified in the contract -> configurable.
SCHEDULE_CRON = "0 4 * * *"
SCHEDULE_TZ = os.getenv("DS4FM2T3_TZ", "Asia/Singapore")


@dataclass(frozen=True)
class SourceTable:
    name: str            # table name (same in RDL_DATA and SDL_DATA)
    csv_file: str
    pk: tuple[str, ...]  # unique key identified from profiling
    timestamp_format: str | None = None


TS_FMT = "%d/%m/%Y %H:%M"   # source files use d/m/yyyy H:MM

SOURCE_TABLES: list[SourceTable] = [
    SourceTable("GEOLOCATION", "olist_geolocation_dataset.csv",
                ("geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
                 "geolocation_city", "geolocation_state")),
    SourceTable("CUSTOMERS", "olist_customers_dataset.csv", ("customer_id",)),
    SourceTable("SELLERS", "olist_sellers_dataset.csv", ("seller_id",)),
    SourceTable("PRODUCTS", "olist_products_dataset.csv", ("product_id",)),
    SourceTable("PRODUCT_CATEGORY_TRANSLATION", "product_category_name_translation.csv",
                ("product_category_name",)),
    SourceTable("ORDERS", "olist_orders_dataset.csv", ("order_id",), TS_FMT),
    SourceTable("ORDER_PAYMENTS", "olist_order_payments_dataset.csv",
                ("order_id", "payment_sequential")),
    SourceTable("ORDER_REVIEWS", "olist_order_reviews_dataset.csv",
                ("review_id", "order_id"), TS_FMT),
    SourceTable("ORDER_ITEMS", "olist_order_items_dataset.csv",
                ("order_id", "order_item_id"), TS_FMT),
]
