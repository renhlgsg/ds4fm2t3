"""Dagster definitions: one asset per pipeline stage, one job, one schedule (04:00 daily).

Start the UI + daemon from the project root:
    dagster dev -m orchestration.definitions
Then in the UI: Automation -> toggle ON the schedule 'daily_incremental_0400'.
(The daemon must be running for schedules to fire; `dagster dev` starts it.)
"""
from __future__ import annotations

from dagster import (AssetSelection, Definitions, ScheduleDefinition, DefaultScheduleStatus,
                     MaterializeResult, MetadataValue, asset, define_asset_job)

from config import settings
from pipeline import clean_sdl, create_database, dq_tests, elt_fdl, ingest_rdl, provision_fdl, provision_rdl


@asset(group_name="ingestion", description="Create DB + schemas + RDL tables, load 9 CSV files into RDL_DATA")
def rdl_raw_tables() -> MaterializeResult:
    create_database.create_database()
    provision_rdl.provision_rdl()
    counts = ingest_rdl.ingest_all()
    ingest_rdl.reconcile(counts)
    return MaterializeResult(metadata={"rows_by_table": MetadataValue.json(counts),
                                       "total_rows": sum(counts.values())})


@asset(deps=[rdl_raw_tables], group_name="cleaning", description="Clean RDL_DATA into SDL_DATA")
def sdl_clean_tables() -> MaterializeResult:
    stats = clean_sdl.clean_all()
    return MaterializeResult(metadata={"clean_stats": MetadataValue.json(stats)})


@asset(deps=[sdl_clean_tables], group_name="warehouse",
       description="Provision FDL_DATA if needed, then initial/incremental load of dimensions and facts")
def fdl_star_schema() -> MaterializeResult:
    provision_fdl.provision_fdl()
    res = elt_fdl.run_elt()
    return MaterializeResult(metadata={
        "inserted": MetadataValue.json({k: v[0] for k, v in res.items()}),
        "updated": MetadataValue.json({k: v[1] for k, v in res.items()}),
        "total_rows": MetadataValue.json({k: v[2] for k, v in res.items()})})


@asset(deps=[fdl_star_schema], group_name="quality",
       description="Run grain/null/duplicate/referential/business DQ tests; fails the run on any ERROR")
def dq_report() -> MaterializeResult:
    results = dq_tests.run_checks()
    failed = dq_tests.summarize(results)
    if failed:
        raise Exception(f"{failed} data-quality ERROR check(s) failed - see FDL_DATA.DQ_RESULT_LOG")
    return MaterializeResult(metadata={
        "checks": len(results),
        "warnings": sum(r["status"] == "WARN" for r in results)})


daily_job = define_asset_job("daily_incremental_job", selection=AssetSelection.all(),
                             description="Ingest -> clean -> incremental ELT -> DQ")

daily_schedule = ScheduleDefinition(
    name="daily_incremental_0400",
    job=daily_job,
    cron_schedule=settings.SCHEDULE_CRON,            # "0 4 * * *"
    execution_timezone=settings.SCHEDULE_TZ,
    default_status=DefaultScheduleStatus.RUNNING,
)

defs = Definitions(assets=[rdl_raw_tables, sdl_clean_tables, fdl_star_schema, dq_report],
                   jobs=[daily_job], schedules=[daily_schedule])
