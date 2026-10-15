# Implementation guide

Everything is run from the project root folder `ds4fm2t3`. Commands are PowerShell. Tested on Linux / Python 3.12; the code uses `pathlib` and no OS-specific calls, but please report any Windows-specific problem.

## Part A - One-time installs
1. **Python 3.11 or 3.12**: https://www.python.org/downloads/ -> download the Windows installer -> run it -> tick **Add python.exe to PATH** -> click **Install Now**. Verify: open PowerShell, type `python --version`.
2. **VS Code**: https://code.visualstudio.com -> install with defaults.
3. **Git**: https://git-scm.com/download/win -> install with defaults.
4. VS Code extensions: press `Ctrl+Shift+X`, search and click **Install** for **Python** (Microsoft), **Jupyter** (Microsoft), **DuckDB SQL Tools** (optional, to browse the database).
5. **WSL**: Refer to instruction in course material.
6. **MiniConda**: Refer to instruction in course material.



## Part B - Open the project and create the environment
1. Open WSL terminal, go to the project root directory: ds4fm2t3, 
   **Expected:** you see `README.md  environment.yml  requirements.txt  src  sql  analysis  app  docs  notebooks  tests ...`
2. 🐧 Create the environment (name is fixed by the requirement: **m2t3**). This takes 3-6 minutes:
   ```bash
   conda env create -f environment.yml
   conda activate m2t3
   python --version          # Expected: Python 3.11.x
   pip list | grep -i -E "duckdb|dagster|meltano|streamlit|pandas"
   ```

> Every later 🐧 command assumes `conda activate m2t3` and `cd ~/ds4fm2t3`. Do this first in every new terminal.


## Part C - Place the source files
Copy the 9 CSV files into `data/raw/`. To keep them elsewhere: `$env:DS4FM2T3_RAW_DIR = "D:\olist\csv"` (same terminal session) or set it permanently with `setx DS4FM2T3_RAW_DIR "D:\olist\csv"` and reopen the terminal.

## Part D - Build the warehouse step by step
Run each command; expected output is described.
| # | Command | What it does | Expected result |
|---|---|---|---|
| 1 | `python -m pipeline.create_database --reset` | creates empty `data\warehouse\ds4fm2t3.duckdb` + schemas | log line "schemas ['FDL_DATA','RDL_DATA','SDL_DATA']" |
| 2 | `python -m pipeline.provision_rdl` | runs `sql\rdl\create_rdl_tables.sql` | "RDL_DATA provisioned: 9 tables" |
| 3 | `python -m pipeline.ingest_rdl` | loads 9 CSV files | 9 row-count lines, then "Ingestion reconciliation OK" |
| 4 | `python -m pipeline.clean_sdl` | creates SDL tables and cleans | GEOLOCATION dups=261831, clean=738332 |
| 5 | `python -m pipeline.provision_fdl` | star-schema DDL + Unknown members | lists D_* and F_* tables |
| 6 | `python -m pipeline.elt_fdl` | initial load | every table `INITIAL`; F_ORDER_ITEMS total=112650 |
| 7 | `python -m pipeline.elt_fdl` (again) | incremental load | every table `INCREMENTAL inserted=0 updated=0` |
| 8 | `python -m pipeline.dq_tests` | 126 checks | "117 passed / 0 failed / 9 warnings", exit code 0 |

Shortcut for steps 1-8: `python -m pipeline.run_all --reset`. Without `--reset` it runs as the daily job does (initial the first time, incremental afterwards).

### Inspect the database
Open `sql` in VS Code with the DuckDB extension, or in the terminal: `python -c "import duckdb; print(duckdb.connect('data/warehouse/ds4fm2t3.duckdb', read_only=True).sql('select * from FDL_DATA.ETL_RUN_LOG order by started_at desc limit 10'))"`.

## Part E - Scheduling with Dagster (04:00 daily)

1. In WSL terminal: conda activate m2t3
2. cd $HOME/ds4fm2t3
3. mkdir -p .dagster_home
   export DAGSTER_HOME=$PWD/.dagster_home
4. dagster dev -m orchestration.definitions

   (keep this terminal open; it starts the web UI **and** the daemon that fires schedules).

5. Browser: http://localhost:3000.
6. Left menu **Assets** -> you see rdl_raw_tables -> sdl_clean_tables -> fdl_star_schema -> dq_report. Click **Materialize all** to run now; open the run to read logs and metadata (row counts, inserted/updated).
7. Left menu **Automation** (older versions: **Overview -> Schedules**) -> row `daily_incremental_0400` shows cron `0 4 * * *` and the time zone. Toggle must be **ON** (it starts ON by default; flip it if it shows OFF).
8. Time zone: set `$env:DS4FM2T3_TZ = "Europe/London"` (any IANA name) before step 2 to change it. Default `Asia/Singapore`.
9. To test the schedule without waiting: Automation -> `daily_incremental_0400` -> **Test Schedule** -> **Evaluate** -> **Launch all**.
For production run `dagster-daemon run` and `dagster-webserver -m orchestration.definitions` as services (e.g. NSSM or Task Scheduler "at startup").

## Part F - Tests
`pytest -q` -> `4 passed` (about 90 s). They rebuild throw-away databases and do not touch `data\warehouse`.

## Part G - Notebook
1. Open `notebooks\01_eda.ipynb` -> top right **Select Kernel -> Python Environments -> m2t3**.
2. **Run All**. To regenerate the notebook from source: `python notebooks/build_notebook.py`.

## Part H - Dashboard
`streamlit run app/streamlit_app.py` -> browser opens http://localhost:8501. Use the sidebar to switch pages. The last page shows data-quality results and ETL runs.

## Part I - Findings, slides, diagrams
* `python -m findings.f1_monthly_sales_trend` (also f2..f5) writes charts to `reports\figures` and tables to `reports\tables`.
* Slides: `slides\Olist_Executive_Summary.pptx`. Rebuild: refresh `slides\deck_data.json` from the findings then `node slides/build_deck.js` (needs `npm i pptxgenjs`).
* Diagrams: https://app.diagrams.net -> **File -> Open from -> Device** -> choose a `.drawio` file in `docs\diagrams`. Excalidraw: https://excalidraw.com -> menu -> **Open** -> `pipeline_system.excalidraw`. These files were generated by `docs/diagrams/build_diagrams.py`; I could not open them in the tools, so re-arrange boxes if any text overflows.

## Part J - GitHub (single `main` branch)
1. Create an empty repository on github.com (**New**, no README).
2. In the terminal:
```
git init -b main
git add .
git commit -m "Initial commit: Olist data warehouse"
git remote add origin https://github.com/<you>/ds4fm2t3.git
git push -u origin main
```
`.gitignore` already excludes the `.duckdb` file and `.venv`. The CSV files are in `data/raw`; remove them from the commit (`git rm -r --cached data/raw`) if the licence or size is a concern.

## Part K - Demonstrating incremental load
1. Run `python -m pipeline.run_all --reset` (initial).
2. Run `python -m pipeline.run_all` -> every table inserted=0 updated=0.
3. Edit a row in `data\raw\olist_orders_dataset.csv` (change one order's `order_status` from `shipped` to `delivered` and fill its delivered date). To add a new order, append consistent rows to the orders, customers, items and payments files.
4. Run `python -m pipeline.run_all` -> F_ORDERS shows `updated=1` (plus any new rows inserted). Check `FDL_DATA.ETL_RUN_LOG`.

## Part L - Troubleshooting
| Symptom | Cause | Fix |
|---|---|---|
| `IOException: Could not set lock on file` | another process (notebook, DB extension, Streamlit mid-query) holds the database | close it, retry; DuckDB allows one writer |
| `FileNotFoundError: Source file not found` | CSV missing / wrong folder | Part C |
| `Conversion Error ... timestamp` during ingest | a CSV date not in `d/m/yyyy H:MM` | fix the file or change `TS_FMT` in `config/settings.py` |
| `ModuleNotFoundError: config` | running from wrong folder | `cd` to project root; use `python -m ...` |
| Dagster schedule never fires | daemon not running or toggle OFF | Part E steps 2 and 5 |
| DQ run exits with code 1 | an ERROR check failed | `select * from FDL_DATA.DQ_RESULT_LOG where status='FAIL'` |
| Streamlit "Database not found" | pipeline not yet run | `python -m pipeline.run_all` |
| Slide build "Cannot find module pptxgenjs" | missing npm package | `npm i pptxgenjs` |
