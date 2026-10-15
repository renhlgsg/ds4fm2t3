"""Builds docs/06_data_dictionary.md straight from sql/fdl/create_fdl_tables.sql so the documented
names / types / sizes can never drift from the real DDL.   Run: python docs/build_data_dictionary.py"""
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ddl = (root / "sql/fdl/create_fdl_tables.sql").read_text(encoding="utf-8")
out = ["# Data dictionary - FDL_DATA (generated from `sql/fdl/create_fdl_tables.sql`)\n",
       "Legend: **PK** primary key, **UK** unique natural key, **FK** logical foreign key (not physically declared - see design document), "
       "**derived** = computed by the ELT. Unknown member: key `-1` exists in every dimension.\n"]
grain = {}
for m in re.finditer(r"--\s*Grain:\s*(.*?)\n(?:--.*\n)*CREATE TABLE IF NOT EXISTS \{schema\}\.(\w+)", ddl):
    grain[m.group(2)] = m.group(1).strip()
for m in re.finditer(r"CREATE TABLE IF NOT EXISTS \{schema\}\.(\w+) \((.*?)\n\);", ddl, re.S):
    name, body = m.group(1), m.group(2)
    if name in ("ETL_RUN_LOG", "DQ_RESULT_LOG") or True:
        pk = re.search(r"PRIMARY KEY \(([^)]*)\)", body)
        pk_cols = [c.strip() for c in pk.group(1).split(",")] if pk else []
        uk = re.search(r"UNIQUE \(([^)]*)\)", body)
        uk_cols = [c.strip() for c in uk.group(1).split(",")] if uk else []
        out.append(f"\n## {name}\n")
        if name in grain:
            out.append(f"**Grain:** {grain[name]}\n")
        out.append("| Column | Type | Key | Nullable | Description / derivation |\n|---|---|---|---|---|")
        for line in body.split("\n"):
            line = line.rstrip()
            if not line.strip() or line.strip().startswith(("PRIMARY KEY", "UNIQUE", "--")):
                continue
            comment = ""
            if "--" in line:
                line, comment = line.split("--", 1)
                comment = comment.strip().replace("|", "/")
            parts = line.strip().rstrip(",").split(None, 1)
            if len(parts) < 2:
                continue
            col, rest = parts
            typ = re.match(r"([A-Z]+(?:\(\d+(?:,\d+)?\))?)", rest).group(1)
            key = "PK" if col in pk_cols else ("UK" if col in uk_cols else ("FK" if col.endswith("_key") and col not in pk_cols else ""))
            nullable = "No" if "NOT NULL" in rest else "Yes"
            if comment.startswith("derived") or "derived" in comment:
                key = (key + " derived").strip()
            out.append(f"| `{col}` | {typ} | {key} | {nullable} | {comment} |")
        if len(pk_cols) > 1:
            out.append(f"\nComposite primary key: ({', '.join(pk_cols)})")
(root / "docs" / "06_data_dictionary.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print("wrote docs/06_data_dictionary.md,", sum(1 for blk in out if blk.lstrip().startswith("## ")), "tables")
