"""Run the whole pipeline end-to-end (what the Dagster 04:00 job does).

    python -m pipeline.run_all            # create DB if absent, ingest, clean, ELT (initial or incremental), DQ
    python -m pipeline.run_all --reset    # drop the database first (forces an INITIAL load)
"""
from __future__ import annotations

import argparse
import sys

from config import settings
from pipeline import clean_sdl, create_database, dq_tests, elt_fdl, ingest_rdl, provision_fdl, provision_rdl
from pipeline.db import log, setup_logging


def run(reset: bool = False, db_path=None, raw_dir=None) -> int:
    create_database.create_database(db_path, reset=reset)
    provision_rdl.provision_rdl(db_path)
    counts = ingest_rdl.ingest_all(db_path, raw_dir)
    ingest_rdl.reconcile(counts, raw_dir)
    clean_sdl.clean_all(db_path)
    provision_fdl.provision_fdl(db_path)
    elt_fdl.run_elt(db_path)
    failures = dq_tests.summarize(dq_tests.run_checks(db_path))
    log.info("PIPELINE %s", "FAILED (DQ errors)" if failures else "SUCCEEDED")
    return failures


if __name__ == "__main__":
    setup_logging()
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    sys.exit(1 if run(reset=ap.parse_args().reset) else 0)
