# ds4fm2t3 - Olist e-commerce data warehouse

End-to-end pipeline: **9 CSV files -> DuckDB (RDL_DATA -> SDL_DATA -> FDL_DATA star schema) -> data-quality gate -> pandas / Streamlit**, scheduled daily at 04:00 with Dagster.

## Quick start 
1. Open WSL terminal, go to the project root directory: ds4fm2t3, 
   **Expected:** you see `README.md  environment.yml  requirements.txt  src  sql  analysis  app  docs  notebooks  tests ...`
2. 🐧 Create the environment (name is fixed by the requirement: **m2t3**). This takes 3-6 minutes:
   ```bash
   conda env create -f environment.yml
   conda activate m2t3
   python --version          # Expected: Python 3.11.x
   pip list | grep -i -E "duckdb|dagster|meltano|streamlit|pandas"
   cd $HOME/ds4fm2t3
   python -m pipeline.run_all --reset        # build everything (~1 min)
   pytest -q                                  # 4 end-to-end tests (~90 s)
   streamlit run app/streamlit_app.py         # dashboard
   mkdir -p .dagster_home
   export DAGSTER_HOME=$PWD/.dagster_home
   dagster dev -m orchestration.definitions   # scheduler UI at http://localhost:3000
   ```

> Every later 🐧 command assumes `conda activate m2t3` and `cd ~/ds4fm2t3`. Do this first in every new terminal.

CSV files are expected in `data/raw/` (or set `DS4FM2T3_RAW_DIR`). Full click-by-click steps: **docs/01_implementation_guide.md**.

## Layout
| Path | Purpose |
|---|---|
| `config/settings.py` | paths, schema names, 9 source tables + unique keys, schedule |
| `sql/rdl`, `sql/sdl`, `sql/fdl` | DDL for the three schemas |
| `sql/elt/*.sql` | one transformation query per dimension/fact |
| `pipeline/` | create_database, provision_rdl, ingest_rdl, clean_sdl, provision_fdl, elt_fdl, dq_tests, run_all |
| `orchestration/definitions.py` | Dagster assets, job, 04:00 schedule |
| `analysis/eda.py`, `notebooks/` | pandas analysis + Jupyter notebook |
| `findings/f1..f5_*.py` | code behind each key finding (one file each) |
| `app/streamlit_app.py` | dashboard |
| `slides/` | executive deck + generator |
| `docs/` | design, lineage, report, traceability, data dictionary, diagrams |
| `tests/` | pytest: DQ pass, idempotency, incremental == full, change capture |

## Documents
1. `docs/01_implementation_guide.md` - build / run / test / troubleshoot / demo
2. `docs/02_design_document.md` - architecture, keys, cleaning, star schema, justification, tool choices
3. `docs/03_data_lineage.md` - lineage tables
4. `docs/04_report.md` - technical approach and findings
5. `docs/05_requirements_traceability.md` - requirement -> code -> test
6. `docs/06_data_dictionary.md` - every column (generated)
7. `docs/diagrams/` - `.drawio` (open in diagrams.net) and `.excalidraw` (open in excalidraw.com)
