// Builds slides/Olist_Executive_Summary.pptx from slides/deck_data.json (numbers produced by findings/*.py)
// Run:  node slides/build_deck.js   (needs: npm i pptxgenjs)
const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");
const D = JSON.parse(fs.readFileSync(path.join(__dirname, "deck_data.json"), "utf8"));
const N = D.nums;
const SKILL = process.env.PPTX_SKILL_DIR || "/mnt/skills/public/pptx";
let applyTheme = null;
try { applyTheme = require(path.join(SKILL, "scripts/apply_theme.js")).applyTheme; } catch (e) { /* optional */ }

const THEME = {
  name: "Olist Ocean", headFontFace: "Cambria", bodyFontFace: "Calibri",
  colors: { dk1: "1B2430", lt1: "FFFFFF", dk2: "0B3C5D", lt2: "EAF1F6",
            accent1: "0B3C5D", accent2: "F28C28", accent3: "3E8EB8", accent4: "2E8B57",
            accent5: "C0392B", accent6: "8A97A5", hlink: "3E8EB8", folHlink: "8A97A5" },
};
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";               // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Olist data warehouse - executive summary";
const C = pres.SchemeColor;
const HEX = { navy: "0B3C5D", orange: "F28C28", blue: "3E8EB8", green: "2E8B57", red: "C0392B", grey: "8A97A5", ice: "EAF1F6", ink: "1B2430" };

pres.defineSlideMaster({
  title: "DARK", background: { color: HEX.navy },
  objects: [],
  slideNumber: undefined,
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: "FFFFFF" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.35, w: 9.0, h: 0.9, fontFace: "Cambria", fontSize: 28, bold: true, color: C.text2, valign: "top", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: 9.2, y: 5.25, w: 0.5, h: 0.25, fontFace: "Calibri", fontSize: 10, color: C.accent6 },
});

const tx = (s, text, o) => s.addText(text, Object.assign({ isTextBox: true, fontFace: "Calibri", color: C.text1, margin: 0 }, o));
const codeNote = (s, file) => tx(s, "Code: " + file, { x: 0.5, y: 5.22, w: 8.5, h: 0.25, fontSize: 10, color: C.accent6, italic: true });
const fmt = (n) => n.toLocaleString("en-US", { maximumFractionDigits: 0 });
const chartBase = { catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt",
  catAxisLabelColor: "55606E", valAxisLabelColor: "55606E", catAxisLabelFontSize: 11, valAxisLabelFontSize: 11,
  valGridLine: { color: "E1E6EB", size: 0.5 }, catGridLine: { style: "none" }, showLegend: false };

// 1 ---- Title
pres.addSection({ title: "Intro" });
let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Intro" });
tx(s, "Olist e-commerce data warehouse", { x: 0.7, y: 1.5, w: 8.6, h: 1.0, fontFace: "Cambria", fontSize: 40, bold: true, color: C.background1 });
tx(s, "From 9 raw CSV files to a star schema, 126 automated quality checks and five decision-ready findings", { x: 0.7, y: 2.65, w: 7.6, h: 0.9, fontSize: 18, color: "CFE3F1" });
tx(s, "Project ds4fm2t3  |  DuckDB, Python, Dagster, Streamlit", { x: 0.7, y: 4.6, w: 8, h: 0.3, fontSize: 12, color: HEX.orange });

// 2 ---- Executive summary
pres.addSection({ title: "Summary" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Summary" });
s.addText("Growth is strong, but retention and delivery speed cap it", { placeholder: "title" });
const stats = [
  [`BRL ${(D.kpis.revenue / 1e6).toFixed(1)}M`, `revenue from ${fmt(D.kpis.orders)} valid orders`, HEX.navy],
  [`+${Math.round(N.f1.ytd_yoy_pct)}%`, "Jan-Aug 2018 revenue vs Jan-Aug 2017", HEX.green],
  [`${N.f3.repeat_rate_pct}%`, "of customers ever buy a second time", HEX.orange],
  [`${N.f4.avg_score_late.toFixed(1)} vs ${N.f4.avg_score_on_time.toFixed(1)}`, "review score: late vs on-time delivery", HEX.red],
];
stats.forEach(([big, label, col], i) => {
  const x = 0.5 + i * 2.28;
  s.addShape(pres.ShapeType.roundRect, { x, y: 1.55, w: 2.1, h: 2.05, fill: { color: HEX.ice }, line: { color: HEX.ice }, rectRadius: 0.12, objectName: "stat-card-" + i });
  tx(s, big, { x: x + 0.1, y: 1.8, w: 1.9, h: 0.75, fontFace: "Cambria", fontSize: 28, bold: true, color: col, align: "center", valign: "middle" });
  tx(s, label, { x: x + 0.15, y: 2.6, w: 1.8, h: 0.8, fontSize: 14, align: "center", valign: "top" });
});
tx(s, [
  { text: "Pipeline: ", options: { bold: true } }, { text: `${D.dq.total} data-quality checks, ${D.dq.fail} failures; ${D.dq.warn} warnings trace to known source-data anomalies.`, options: { breakLine: true } },
  { text: "Recommendation: ", options: { bold: true } }, { text: "fund a retention programme and a regional logistics fix before more acquisition spend." },
], { x: 0.5, y: 3.95, w: 9.0, h: 1.0, fontSize: 15, paraSpaceAfter: 6 });

// 3 ---- Architecture
pres.addSection({ title: "Solution" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Solution" });
s.addText("One pipeline, three layers, one schedule", { placeholder: "title" });
const boxes = [["9 CSV files", "olist_*.csv", HEX.grey], ["RDL_DATA", "raw, 1:1 with files", HEX.blue], ["SDL_DATA", "cleaned, PKs enforced", HEX.blue],
               ["FDL_DATA", "star schema 6 dims + 4 facts", HEX.navy], ["Consumers", "Streamlit, notebooks, slides", HEX.orange]];
boxes.forEach(([t, sub, col], i) => {
  const x = 0.5 + i * 1.86;
  s.addShape(pres.ShapeType.roundRect, { x, y: 1.6, w: 1.6, h: 1.25, fill: { color: col }, line: { color: col }, rectRadius: 0.1, objectName: "layer-" + i });
  tx(s, t, { x: x + 0.08, y: 1.7, w: 1.44, h: 0.4, fontFace: "Cambria", fontSize: 15, bold: true, color: C.background1, align: "center" });
  tx(s, sub, { x: x + 0.08, y: 2.15, w: 1.44, h: 0.6, fontSize: 12, color: C.background1, align: "center" });
  if (i < 4) s.addShape(pres.ShapeType.rightArrow, { x: x + 1.62, y: 2.05, w: 0.22, h: 0.28, fill: { color: HEX.grey }, line: { color: HEX.grey }, objectName: "arrow-" + i });
});
s.addShape(pres.ShapeType.roundRect, { x: 0.5, y: 3.15, w: 9.0, h: 0.5, fill: { color: HEX.ice }, line: { color: HEX.ice }, rectRadius: 0.08, objectName: "dagster-band" });
tx(s, "Dagster schedule  0 4 * * *  -  ingest, clean, incremental ELT, data-quality gate", { x: 0.7, y: 3.15, w: 8.6, h: 0.5, fontSize: 14, bold: true, color: C.text2, valign: "middle" });
tx(s, [
  { text: "Incremental by design: ", options: { bold: true } }, { text: "row-hash change detection inserts new rows and updates changed ones; a re-run with no new data changes nothing.", options: { breakLine: true } },
  { text: "Proven by test: ", options: { bold: true } }, { text: "an initial partial load plus an incremental top-up equals a one-shot full load." },
], { x: 0.5, y: 3.95, w: 9.0, h: 1.0, fontSize: 14, paraSpaceAfter: 6 });

// 4 ---- Star schema
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Solution" });
s.addText("Four facts share six conformed dimensions", { placeholder: "title" });
const facts = [["F_ORDER_ITEMS", "1 row per order item"], ["F_ORDERS", "1 row per order"], ["F_ORDER_PAYMENTS", "1 row per payment"], ["F_ORDER_REVIEWS", "1 row per review"]];
facts.forEach(([n, g], i) => {
  const x = 0.5 + i * 2.28;
  s.addShape(pres.ShapeType.roundRect, { x, y: 1.5, w: 2.1, h: 1.05, fill: { color: HEX.navy }, line: { color: HEX.navy }, rectRadius: 0.1, objectName: "fact-" + i });
  tx(s, n, { x: x + 0.05, y: 1.6, w: 2.0, h: 0.4, fontSize: 14, bold: true, color: C.background1, align: "center" });
  tx(s, g, { x: x + 0.05, y: 2.05, w: 2.0, h: 0.35, fontSize: 12, color: "CFE3F1", align: "center" });
});
const dims = ["D_DATE", "D_CUSTOMER", "D_PRODUCT", "D_SELLER", "D_GEOGRAPHY", "D_PAYMENT_TYPE"];
dims.forEach((n, i) => {
  const x = 0.5 + i * 1.5;
  s.addShape(pres.ShapeType.roundRect, { x, y: 3.1, w: 1.38, h: 0.6, fill: { color: HEX.ice }, line: { color: HEX.blue }, rectRadius: 0.08, objectName: "dim-" + i });
  tx(s, n, { x: x + 0.03, y: 3.1, w: 1.32, h: 0.6, fontSize: 12, bold: true, color: C.text2, align: "center", valign: "middle" });
});
tx(s, [
  { text: "Why this shape: ", options: { bold: true } }, { text: "each fact has one grain and additive measures; customers are keyed on the real person (unique id), not the per-order id, so lifetime value is correct.", options: { breakLine: true } },
  { text: "Derived columns: ", options: { bold: true } }, { text: "total_sale_amount, customer_lifetime_value, delivery_days, is_late, review flags and more." },
], { x: 0.5, y: 4.0, w: 9.0, h: 1.1, fontSize: 14, paraSpaceAfter: 6 });

// 5 ---- Finding 1
pres.addSection({ title: "Findings" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText(`Revenue grew ${Math.round(N.f1.ytd_yoy_pct)}% year on year, then plateaued`, { placeholder: "title" });
s.addChart([{ type: pres.charts.BAR, data: [{ name: "Revenue (BRL k)", labels: D.monthly.labels, values: D.monthly.revenue_k }], options: { chartColors: [HEX.navy], barGapWidthPct: 40 } },
            { type: pres.charts.LINE, data: [{ name: "3-month average", labels: D.monthly.labels, values: D.monthly.avg3_k }], options: { chartColors: [HEX.orange], lineSize: 2.5, lineDataSymbol: "none" } }],
  Object.assign({}, chartBase, { x: 0.4, y: 1.3, w: 6.2, h: 3.8, showTitle: true, title: "Monthly revenue, BRL thousand", titleFontSize: 12, titleColor: "55606E", titleFontFace: "+mn-lt", catAxisLabelRotate: 315, catAxisLabelFontSize: 9, showLegend: true, legendPos: "b", legendFontFace: "+mn-lt", legendFontSize: 10 }));
tx(s, [
  { text: `Peak: ${N.f1.peak_month}`, options: { bold: true, breakLine: true } },
  { text: `${fmt(N.f1.peak_orders)} orders, BRL ${fmt(N.f1.peak_revenue)}`, options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "Since early 2018", options: { bold: true, breakLine: true } },
  { text: "Monthly revenue has stayed between BRL 0.84M and 0.99M; growth has stalled.", options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "Data note", options: { bold: true, breakLine: true } },
  { text: "Sep-2016, Dec-2016 and Sep-2018 hold under 100 orders and are excluded." },
], { x: 6.9, y: 1.5, w: 2.6, h: 3.4, fontSize: 14 });
codeNote(s, "findings/f1_monthly_sales_trend.py");

// 6 ---- Finding 2
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("Demand is broad across categories, concentrated in sellers", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Share of revenue (%)", labels: D.cats.labels, values: D.cats.values }],
  Object.assign({}, chartBase, { x: 0.4, y: 1.35, w: 5.9, h: 3.75, barDir: "bar", chartColors: [HEX.navy], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelColor: "55606E", dataLabelFontSize: 10,
    showTitle: true, title: "Top 10 categories, % of revenue", titleFontSize: 12, titleColor: "55606E", titleFontFace: "+mn-lt", valAxisHidden: true, valGridLine: { style: "none" } }));
tx(s, `${N.f2.top10pct_sellers_revenue_share.toFixed(0)}%`, { x: 6.6, y: 1.5, w: 2.9, h: 0.8, fontFace: "Cambria", fontSize: 44, bold: true, color: HEX.orange });
tx(s, `of revenue comes from the top 10% of ${fmt(N.f2.n_sellers_with_sales)} sellers`, { x: 6.6, y: 2.35, w: 2.9, h: 0.8, fontSize: 14 });
tx(s, `No category exceeds ${Math.ceil(N.f2.top_category_share)}% of revenue; the top five together make up ${N.f2.top5_category_share.toFixed(0)}%.`, { x: 6.6, y: 3.4, w: 2.9, h: 1.3, fontSize: 14 });
codeNote(s, "findings/f2_top_products.py");

// 7 ---- Finding 3
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText(`${(100 - N.f3.repeat_rate_pct).toFixed(0)}% of customers buy once; one-time big spenders matter most`, { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "% of customers", labels: D.seg.labels, values: D.seg.cust }, { name: "% of lifetime revenue", labels: D.seg.labels, values: D.seg.rev }],
  Object.assign({}, chartBase, { x: 0.4, y: 1.4, w: 6.1, h: 3.7, barDir: "col", barGrouping: "clustered", chartColors: [HEX.grey, HEX.navy], showLegend: true, legendPos: "b", legendFontFace: "+mn-lt", legendFontSize: 10, catAxisLabelFontSize: 9, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", dataLabelFontSize: 9, dataLabelColor: "55606E", valAxisHidden: true, valGridLine: { style: "none" } }));
tx(s, [
  { text: `Big-ticket one-time buyers`, options: { bold: true, breakLine: true } },
  { text: `${N.f3.top_segment_customer_pct.toFixed(0)}% of customers deliver ${N.f3.top_segment_revenue_pct.toFixed(0)}% of revenue.`, options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "Repeat buyers", options: { bold: true, breakLine: true } },
  { text: `Worth BRL ${N.f3.avg_clv_repeat.toFixed(0)} each vs BRL ${N.f3.avg_clv_one_time.toFixed(0)} for one-time buyers, yet only ${N.f3.repeat_rate_pct}% of customers.` },
], { x: 6.8, y: 1.5, w: 2.7, h: 3.4, fontSize: 14 });
codeNote(s, "findings/f3_customer_segmentation.py");

// 8 ---- Finding 4
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("Late delivery halves the review score", { placeholder: "title" });
s.addChart(pres.charts.BAR, [{ name: "Average review score", labels: D.delay.labels, values: D.delay.score }],
  Object.assign({}, chartBase, { x: 0.4, y: 1.35, w: 5.9, h: 3.75, barDir: "col", chartColors: [HEX.green, HEX.green, HEX.orange, HEX.red], valAxisMinVal: 1, valAxisMaxVal: 5, showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", dataLabelColor: "55606E", dataLabelFontSize: 11,
    showTitle: true, title: "Avg review score by delivery vs promised date", titleFontSize: 12, titleColor: "55606E", titleFontFace: "+mn-lt", catAxisLabelFontSize: 10, invertedColors: [HEX.green, HEX.green, HEX.orange, HEX.red] }));
tx(s, `${N.f4.avg_score_on_time.toFixed(1)} \u2192 ${N.f4.avg_score_late.toFixed(1)}`, { x: 6.6, y: 1.5, w: 2.9, h: 0.7, fontFace: "Cambria", fontSize: 36, bold: true, color: HEX.red });
tx(s, `average score, on-time vs late; ${N.f4.negative_pct_late.toFixed(0)}% of late orders get a 1-2 star review (${N.f4.negative_pct_on_time.toFixed(0)}% when on time)`, { x: 6.6, y: 2.25, w: 2.9, h: 1.2, fontSize: 14 });
tx(s, `Distance matters: ${N.f4.slowest_big_state} waits ${N.f4.slowest_big_state_days.toFixed(0)} days on average, ${N.f4.fastest_state} just ${N.f4.fastest_state_days.toFixed(0)}.`, { x: 6.6, y: 3.6, w: 2.9, h: 1.1, fontSize: 14 });
codeNote(s, "findings/f4_delivery_and_reviews.py");

// 9 ---- Finding 5
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Findings" });
s.addText("Cards dominate payment; the Southeast dominates demand", { placeholder: "title" });
s.addChart(pres.charts.DOUGHNUT, [{ name: "Payment value", labels: D.pay.labels, values: D.pay.values }],
  { x: 0.4, y: 1.35, w: 4.4, h: 3.75, chartColors: [HEX.navy, HEX.orange, HEX.grey], showPercent: true, showLegend: true, legendPos: "b", legendFontFace: "+mn-lt", legendFontSize: 11, dataLabelColor: "FFFFFF", dataLabelFontFace: "+mn-lt", dataLabelFontSize: 11, holeSize: 55,
    showTitle: true, title: "Share of payment value", titleFontSize: 12, titleColor: "55606E", titleFontFace: "+mn-lt" });
tx(s, `${N.f5.credit_card_value_pct.toFixed(0)}%`, { x: 5.2, y: 1.5, w: 1.9, h: 0.8, fontFace: "Cambria", fontSize: 40, bold: true, color: HEX.navy });
tx(s, `of value paid by credit card, in ${N.f5.credit_card_avg_installments.toFixed(1)} instalments on average`, { x: 5.2, y: 2.3, w: 1.95, h: 1.3, fontSize: 13 });
tx(s, `${N.f5.southeast_pct.toFixed(0)}%`, { x: 7.4, y: 1.5, w: 2.1, h: 0.8, fontFace: "Cambria", fontSize: 40, bold: true, color: HEX.orange });
tx(s, `of revenue from the Southeast; ${N.f5.top_state} alone is ${N.f5.top_state_pct.toFixed(0)}%`, { x: 7.4, y: 2.3, w: 2.1, h: 1.3, fontSize: 13 });
tx(s, "Instalments are widely used, so card-partner offers are worth testing as a conversion lever.", { x: 5.2, y: 3.9, w: 4.3, h: 1.0, fontSize: 14 });
codeNote(s, "findings/f5_payments_and_geography.py");

// 10 ---- Data quality
pres.addSection({ title: "Trust" });
s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Trust" });
s.addText(`${D.dq.total} automated checks pass; ${D.dq.warn} warnings are source-data defects`, { placeholder: "title" });
const rows = [["Source anomaly found by the tests", "Rows"], ["Carrier hand-over dated before approval", "1,358"], ["Payments differ from items + freight by more than 1.00", "250"],
  ["Carrier hand-over dated before purchase", "161"], ["Delivery dated before carrier hand-over", "23"], ["Order marked delivered but no delivery date", "8"]];
s.addTable(rows.map((r, i) => r.map((c, j) => ({ text: c, options: { bold: i === 0, color: i === 0 ? "FFFFFF" : "1B2430", fill: { color: i === 0 ? HEX.navy : (i % 2 ? "FFFFFF" : HEX.ice) }, align: j ? "right" : "left", fontFace: "Calibri", fontSize: 13 } }))),
  { x: 0.5, y: 1.4, w: 5.6, colW: [4.6, 1.0], rowH: 0.42, border: { type: "none" } });
tx(s, [
  { text: "How it is handled", options: { bold: true, breakLine: true } },
  { text: "Hard rules (keys, grain, totals, referential integrity) fail the run. Known source defects are reported, not hidden, and never silently dropped.", options: { breakLine: true } },
  { text: " ", options: { breakLine: true } },
  { text: "Results are stored in FDL_DATA.DQ_RESULT_LOG and shown in the dashboard." },
], { x: 6.4, y: 1.4, w: 3.1, h: 3.4, fontSize: 14 });
codeNote(s, "pipeline/dq_tests.py");

// 11 ---- Recommendations
pres.addSection({ title: "Next steps" });
s = pres.addSlide({ masterName: "DARK", sectionTitle: "Next steps" });
tx(s, "What to do next", { x: 0.7, y: 0.6, w: 8.6, h: 0.8, fontFace: "Cambria", fontSize: 36, bold: true, color: C.background1 });
const recs = [["1", "Launch a retention programme", `Move the ${N.f3.repeat_rate_pct}% repeat rate: target big-ticket one-time buyers with a second-purchase offer.`],
              ["2", "Fix regional delivery promises", "Re-set estimates and add carriers for the North and Northeast, where waits are 2-3x longer."],
              ["3", "Reduce seller concentration risk", "Onboard and develop mid-tier sellers; two thirds of revenue sits with the top 10%."]];
recs.forEach(([n, h, t], i) => {
  const y = 1.7 + i * 1.05;
  s.addShape(pres.ShapeType.ellipse, { x: 0.7, y, w: 0.6, h: 0.6, fill: { color: HEX.orange }, line: { color: HEX.orange }, objectName: "rec-badge-" + n });
  tx(s, n, { x: 0.7, y, w: 0.6, h: 0.6, fontFace: "Cambria", fontSize: 22, bold: true, color: C.background1, align: "center", valign: "middle" });
  tx(s, h, { x: 1.55, y: y - 0.02, w: 7.8, h: 0.35, fontSize: 18, bold: true, color: C.background1 });
  tx(s, t, { x: 1.55, y: y + 0.36, w: 7.8, h: 0.5, fontSize: 14, color: "CFE3F1" });
});

(async () => {
  const out = path.join(__dirname, "Olist_Executive_Summary.pptx");
  await pres.writeFile({ fileName: out });
  if (applyTheme) await applyTheme(out, THEME);
  console.log("wrote", out);
})();
