"""Generates the diagram SOURCE files so they are reproducible and diff-able:
    architecture.drawio / star_schema.drawio / pipeline_architecture.drawio   -> open in https://app.diagrams.net (or draw.io desktop)
    pipeline_system.excalidraw                                              -> open / drag into https://excalidraw.com
Run:  python docs/diagrams/build_diagrams.py
"""
from __future__ import annotations

import json
import random
from html import escape
from pathlib import Path

OUT = Path(__file__).parent


# ----------------------------------------------------------------- draw.io helpers
class Page:
    def __init__(self, name):
        self.name, self.cells, self._n = name, [], 1

    def box(self, x, y, w, h, label, fill="#dae8fc", stroke="#6c8ebf", font=12, bold=False, shape="rounded=1;"):
        self._n += 1
        cid = f"c{self._n}"
        txt = f"<b>{escape(label)}</b>" if bold else escape(label)
        txt = txt.replace("\n", "<br>")
        style = (f"{shape}whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontSize={font};"
                 "verticalAlign=top;align=left;spacingLeft=6;spacingTop=4;")
        self.cells.append(f'<mxCell id="{cid}" value="{escape(txt, quote=True)}" style="{style}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def label(self, x, y, w, h, text, font=14, bold=True):
        self._n += 1
        cid = f"c{self._n}"
        t = f"<b>{escape(text)}</b>" if bold else escape(text)
        style = f"text;html=1;fontSize={font};align=center;verticalAlign=middle;"
        self.cells.append(f'<mxCell id="{cid}" value="{escape(t, quote=True)}" style="{style}" vertex="1" parent="1">'
                          f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

    def edge(self, a, b, text="", dashed=False):
        self._n += 1
        cid = f"c{self._n}"
        style = "endArrow=block;html=1;rounded=0;strokeWidth=1.5;" + ("dashed=1;" if dashed else "")
        self.cells.append(f'<mxCell id="{cid}" value="{escape(text, quote=True)}" style="{style}" edge="1" parent="1" '
                          f'source="{a}" target="{b}"><mxGeometry relative="1" as="geometry"/></mxCell>')

    def xml(self, idx):
        body = "".join(self.cells)
        return (f'<diagram id="p{idx}" name="{escape(self.name)}"><mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" '
                f'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="900">'
                f'<root><mxCell id="0"/><mxCell id="1" parent="0"/>{body}</root></mxGraphModel></diagram>')


def write_drawio(name, pages):
    xml = '<mxfile host="app.diagrams.net">' + "".join(p.xml(i) for i, p in enumerate(pages)) + "</mxfile>"
    (OUT / name).write_text(xml, encoding="utf-8")


# ----------------------------------------------------------------- 1. architecture
a = Page("Solution architecture")
a.label(40, 10, 1300, 30, "Olist data warehouse - solution architecture (project ds4fm2t3)", 18)
src = a.box(40, 120, 220, 330, "Source (Windows file system)\n\nolist_geolocation_dataset.csv\nolist_customers_dataset.csv\nolist_sellers_dataset.csv\nolist_products_dataset.csv\nproduct_category_name_translation.csv\nolist_orders_dataset.csv\nolist_order_payments_dataset.csv\nolist_order_reviews_dataset.csv\nolist_order_items_dataset.csv", "#f5f5f5", "#666666", 11, shape="rounded=0;")
db = a.box(330, 70, 700, 430, "", "#fff2cc", "#d6b656", 12, shape="rounded=1;arcSize=3;")
a.label(340, 75, 680, 24, "DuckDB file  data/warehouse/ds4fm2t3.duckdb", 13)
rdl = a.box(350, 130, 190, 300, "RDL_DATA (raw)\n\n9 tables, 1:1 with CSV\nno PK constraints\ntyped columns\nfull refresh per run", "#dae8fc", "#6c8ebf", 12, True)
sdl = a.box(570, 130, 190, 300, "SDL_DATA (clean)\n\n9 tables, PKs enforced\nmissing PK row: deleted\nnumeric NULL: 0\nstring NULL: 'Unspecified'\nduplicates: removed", "#d5e8d4", "#82b366", 12, True)
fdl = a.box(790, 130, 220, 300, "FDL_DATA (star schema)\n\n6 dimensions D_*\n4 facts F_*\nETL_RUN_LOG\nDQ_RESULT_LOG\nincremental by row_hash", "#e1d5e7", "#9673a6", 12, True)
dag = a.box(330, 530, 700, 70, "Dagster: asset graph rdl_raw_tables -> sdl_clean_tables -> fdl_star_schema -> dq_report\nschedule daily_incremental_0400  (cron 0 4 * * *)", "#ffe6cc", "#d79b00", 12, True)
dq = a.box(1090, 130, 250, 110, "Data-quality gate\npipeline/dq_tests.py\n126 checks: grain, null, duplicate,\nreferential, business", "#f8cecc", "#b85450", 11, True)
st = a.box(1090, 280, 250, 80, "Streamlit dashboard\napp/streamlit_app.py", "#dae8fc", "#6c8ebf", 12, True)
nb = a.box(1090, 390, 250, 60, "Jupyter notebook + pandas\nnotebooks/01_eda.ipynb", "#dae8fc", "#6c8ebf", 12, True)
sl = a.box(1090, 480, 250, 60, "Slides + findings code\nslides/, findings/*.py", "#dae8fc", "#6c8ebf", 12, True)
a.edge(src, rdl, "ingest_rdl.py"); a.edge(rdl, sdl, "clean_sdl.py"); a.edge(sdl, fdl, "elt_fdl.py (SQL in sql/elt)")
a.edge(fdl, dq); a.edge(fdl, st); a.edge(fdl, nb); a.edge(fdl, sl)
a.edge(dag, db, "orchestrates", True)

# ----------------------------------------------------------------- 2. star schema
s = Page("Star schema")
s.label(40, 10, 1300, 30, "FDL_DATA star schema (PK = primary key, FK = logical foreign key, * = derived column)", 18)
def dim(x, y, name, rows, h=170):
    return s.box(x, y, 250, h, f"{name}\n" + "\n".join(rows), "#e1d5e7", "#9673a6", 11, True)
dd = dim(40, 60, "D_DATE", ["PK date_key INTEGER", "full_date DATE", "day_of_week, day_name", "month_number, month_name", "year_month VARCHAR(7)", "quarter, year, is_weekend"])
dc = dim(40, 280, "D_CUSTOMER", ["PK customer_key BIGINT", "UK customer_unique_id VARCHAR(32)", "zip_code_prefix, city, state", "* first/last_purchase_date", "* total_orders, total_items", "* customer_lifetime_value DEC(14,2)", "* average_order_value, is_repeat"], 190)
dp = dim(40, 510, "D_PRODUCT", ["PK product_key BIGINT", "UK product_id VARCHAR(32)", "category_name_pt / _en", "name_length, description_length", "photos_qty, weight_g, L/H/W cm", "* volume_cm3, weight_class"], 170)
dg = dim(1090, 60, "D_GEOGRAPHY", ["PK geography_key BIGINT", "UK zip_code_prefix INTEGER", "city, state, * region", "latitude, longitude (centroid)", "* has_coordinates"], 150)
ds = dim(1090, 250, "D_SELLER", ["PK seller_key BIGINT", "UK seller_id VARCHAR(32)", "zip_code_prefix, city, state"], 110)
dpt = dim(1090, 400, "D_PAYMENT_TYPE", ["PK payment_type_key BIGINT", "UK payment_type_code VARCHAR(20)", "payment_type_name", "* payment_method_group"], 120)
fi = s.box(380, 60, 300, 270, "F_ORDER_ITEMS  (grain: order item)\nPK order_id, order_item_id\nFK purchase_date_key, shipping_limit_date_key\nFK customer_key, product_key, seller_key\nFK customer_geography_key, seller_geography_key\norder_status (degenerate)\n* item_quantity\nprice, freight_value DEC(10,2)\n* total_sale_amount = price + freight\n* freight_ratio", "#fff2cc", "#d6b656", 11, True)
fo = s.box(720, 60, 330, 330, "F_ORDERS  (grain: order; accumulating snapshot)\nPK order_id\nFK customer_key, customer_geography_key\nFK purchase / approved / carrier /\n   delivered / estimated_delivery _date_key\norder_status, *_ts timestamps\n* item_count, seller_count\n* total_price, total_freight\n* total_order_amount, total_payment_value\n* approval_hours, carrier_handover_days\n* delivery_days, delivery_delay_days\n* is_delivered, is_late", "#fff2cc", "#d6b656", 11, True)
fp = s.box(380, 400, 300, 200, "F_ORDER_PAYMENTS  (grain: payment record)\nPK order_id, payment_sequential\nFK purchase_date_key, customer_key,\n   payment_type_key\npayment_installments\npayment_value DEC(12,2)\n* installment_value", "#fff2cc", "#d6b656", 11, True)
fr = s.box(720, 430, 330, 220, "F_ORDER_REVIEWS  (grain: review of an order)\nPK review_id, order_id\nFK customer_key, review_creation_date_key,\n   review_answer_date_key\nreview_score SMALLINT\n* has_comment_title/message, comment_message_length\n* response_time_hours\n* is_positive, is_negative", "#fff2cc", "#d6b656", 11, True)
for f_, d_ in [(fi, dd), (fi, dc), (fi, dp), (fi, ds), (fi, dg), (fo, dd), (fo, dc), (fo, dg), (fp, dd), (fp, dc), (fp, dpt), (fr, dd), (fr, dc)]:
    s.edge(f_, d_)

# ----------------------------------------------------------------- 3. pipeline architecture
p = Page("Pipeline architecture")
p.label(40, 10, 1300, 30, "Pipeline architecture - one daily Dagster run (04:00)", 18)
steps = [("1  rdl_raw_tables", "create_database.py\nprovision_rdl.py (DDL)\ningest_rdl.py\nread_csv with explicit types\nDELETE+INSERT per table\nreconcile CSV rows = RDL rows", "#dae8fc", "#6c8ebf"),
         ("2  sdl_clean_tables", "clean_sdl.py\nread RDL column metadata\ndrop rows missing PK\nCOALESCE numeric 0 / string\nSELECT DISTINCT\nPK tie-break safety net", "#d5e8d4", "#82b366"),
         ("3  fdl_star_schema", "provision_fdl.py (DDL + -1 members)\nelt_fdl.py: dims then facts\nstage -> md5 row_hash\nUPDATE changed rows\nINSERT new rows\nlog to ETL_RUN_LOG", "#e1d5e7", "#9673a6"),
         ("4  dq_report", "dq_tests.py\n126 SQL checks -> violation count\nERROR fails the run\nWARN = known source anomaly\nresults to DQ_RESULT_LOG", "#f8cecc", "#b85450")]
ids = []
for i, (t, body, f_, s_) in enumerate(steps):
    ids.append(p.box(40 + i * 330, 90, 290, 230, t + "\n\n" + body, f_, s_, 12, True))
for i in range(3):
    p.edge(ids[i], ids[i + 1])
p.box(40, 380, 1280, 120, "Incremental logic (per target table)\n1) materialise sql/elt/<target>.sql into TEMP stg   2) row_hash = md5(all columns)   3) UPDATE target WHERE natural key matches AND row_hash differs   4) INSERT staged rows whose natural key is absent\nInitial load = target holds only the -1 Unknown member; every later run is incremental. Re-running with unchanged data inserts 0 and updates 0 rows.", "#fff2cc", "#d6b656", 12, True)
p.box(40, 540, 1280, 80, "Failure handling: each table loads inside a transaction (ROLLBACK on error) | Dagster run fails if a stage raises or a DQ ERROR check fails | all runs are recorded in FDL_DATA.ETL_RUN_LOG", "#f5f5f5", "#666666", 12, False)

write_drawio("architecture.drawio", [a])
write_drawio("star_schema.drawio", [s])
write_drawio("pipeline_architecture.drawio", [p])


# ----------------------------------------------------------------- Excalidraw
random.seed(7)
els = []


def _base(t, x, y, w, h, **kw):
    e = {"id": f"e{len(els)+1:03d}", "type": t, "x": x, "y": y, "width": w, "height": h, "angle": 0,
         "strokeColor": "#1e1e1e", "backgroundColor": "transparent", "fillStyle": "solid", "strokeWidth": 2,
         "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [], "frameId": None,
         "roundness": {"type": 3} if t == "rectangle" else None, "seed": random.randint(1, 2**31),
         "version": 1, "versionNonce": random.randint(1, 2**31), "isDeleted": False, "boundElements": None,
         "updated": 1, "link": None, "locked": False}
    e.update(kw)
    els.append(e)
    return e


def xbox(x, y, w, h, title, body, bg):
    _base("rectangle", x, y, w, h, backgroundColor=bg)
    xtext(x + 12, y + 10, w - 24, title, 20, bold=True)
    xtext(x + 12, y + 44, w - 24, body, 14)


def xtext(x, y, w, text, size, bold=False):
    lines = text.count("\n") + 1
    h = int(size * 1.25 * lines)
    _base("text", x, y, w, h, text=text, fontSize=size, fontFamily=1, textAlign="left", verticalAlign="top",
          containerId=None, originalText=text, lineHeight=1.25, baseline=int(size * 1.1), roundness=None)


def xarrow(x1, y1, x2, y2):
    _base("arrow", x1, y1, x2 - x1, y2 - y1, points=[[0, 0], [x2 - x1, y2 - y1]], lastCommittedPoint=None,
          startBinding=None, endBinding=None, startArrowhead=None, endArrowhead="arrow", roundness={"type": 2})


xtext(40, 10, 900, "Olist data pipeline - system architecture", 28, True)
xbox(40, 90, 230, 230, "9 CSV files", "olist_*.csv (8)\nproduct_category_\nname_translation.csv\n\nWindows folder\n(DS4FM2T3_RAW_DIR)", "#e9ecef")
xbox(330, 90, 230, 230, "RDL_DATA", "raw tables (9)\ntyped, no PKs\nfull refresh\n\nDuckDB schema", "#a5d8ff")
xbox(620, 90, 230, 230, "SDL_DATA", "clean tables (9)\nPKs enforced\nNULL rules, dedup\n\nDuckDB schema", "#b2f2bb")
xbox(910, 90, 270, 230, "FDL_DATA", "6 dimensions D_*\n4 facts F_*\nincremental (row_hash)\nETL + DQ logs\n\nDuckDB schema", "#d0bfff")
for x in (270, 560, 850):
    xarrow(x + 2, 205, x + 58, 205)
xbox(330, 380, 520, 130, "Dagster  (daily 04:00)", "assets: rdl_raw_tables -> sdl_clean_tables\n-> fdl_star_schema -> dq_report\nschedule: daily_incremental_0400", "#ffd8a8")
xarrow(590, 380, 590, 322)
xbox(910, 380, 270, 130, "Data-quality gate", "126 checks\nERROR fails the run\nWARN = source anomaly", "#ffc9c9")
xarrow(1045, 322, 1045, 378)
xbox(40, 380, 250, 130, "Consumers", "Streamlit dashboard\nJupyter + pandas\nSlides / findings code", "#a5d8ff")
xarrow(1000, 322, 160, 378)
(OUT / "pipeline_system.excalidraw").write_text(json.dumps({
    "type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": els,
    "appState": {"gridSize": None, "viewBackgroundColor": "#ffffff"}, "files": {}}, indent=1), encoding="utf-8")
print("wrote:", *sorted(p.name for p in OUT.iterdir() if p.suffix in (".drawio", ".excalidraw")))
