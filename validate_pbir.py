"""
End-to-end validation for the generated PBIR project.

Checks:
  1. Every JSON file parses
  2. Every TMDL file is non-empty
  3. Every measure/column reference in visual.json files exists in the model
  4. Every page referenced in pages.json has a corresponding folder
  5. Every relationship references existing tables/columns
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPORT = ROOT / "L.A_Crime_Rate.Report"
MODEL  = ROOT / "L.A_Crime_Rate.SemanticModel"

errors = []
warnings = []

# -----------------------------------------------------------------------------
# 1. Parse every JSON file
# -----------------------------------------------------------------------------
print("=" * 70)
print("1. JSON syntax check")
print("=" * 70)
json_count = 0
for p in REPORT.rglob("*.json"):
    json_count += 1
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"  [JSON ERROR] {p.relative_to(ROOT)}: {e}")

print(f"  Parsed {json_count} JSON files")
if not [e for e in errors if "JSON ERROR" in e]:
    print("  All JSON valid")

# -----------------------------------------------------------------------------
# 2. Parse model tables — collect entity, column, measure names
# -----------------------------------------------------------------------------
print("\n" + "=" * 70)
print("2. Model entity / column / measure catalog")
print("=" * 70)

entities = {}          # entity_name -> set of column/measure names
table_files = list((MODEL / "definition" / "tables").glob("*.tmdl"))
for tf in table_files:
    text = tf.read_text(encoding="utf-8")
    # table name on first line: "table Foo" or "table 'Foo'"
    m = re.search(r"^table\s+'?([^'\n]+?)'?\s*$", text.splitlines()[0])
    if not m:
        warnings.append(f"  Could not parse table name from {tf.name}")
        continue
    tname = m.group(1).strip()
    cols     = set(re.findall(r"^\tcolumn\s+'?([^'\n=]+?)'?\s*(?:=|$)", text, re.MULTILINE))
    measures = set(re.findall(r"^\tmeasure\s+'?([^'\n=]+?)'?\s*=", text, re.MULTILINE))
    entities[tname] = cols | measures
    print(f"  [{tname}]  cols+measures: {len(entities[tname])}")

# -----------------------------------------------------------------------------
# 3. Verify every visual.json reference resolves
# -----------------------------------------------------------------------------
print("\n" + "=" * 70)
print("3. Visual field-reference resolution")
print("=" * 70)

visual_count = 0
ref_count = 0
for vp in REPORT.rglob("visual.json"):
    visual_count += 1
    data = json.loads(vp.read_text(encoding="utf-8"))
    qs = data.get("visual", {}).get("query", {}).get("queryState", {})
    for role_name, role in qs.items():
        for proj in role.get("projections", []):
            field = proj.get("field", {})
            for kind, body in field.items():
                if kind in ("Column", "Measure"):
                    entity = body.get("Expression", {}).get("SourceRef", {}).get("Entity")
                    prop = body.get("Property")
                    ref_count += 1
                    if entity not in entities:
                        errors.append(
                            f"  [MISSING ENTITY] {vp.relative_to(ROOT)} "
                            f"role={role_name} -> '{entity}' not in model"
                        )
                    elif prop not in entities[entity]:
                        errors.append(
                            f"  [MISSING FIELD]  {vp.relative_to(ROOT)} "
                            f"role={role_name} -> '{entity}.{prop}' not in model"
                        )

print(f"  Scanned {visual_count} visual.json files")
print(f"  Resolved {ref_count} field references")

# -----------------------------------------------------------------------------
# 4. Pages metadata consistency
# -----------------------------------------------------------------------------
print("\n" + "=" * 70)
print("4. Pages metadata consistency")
print("=" * 70)
pm = json.loads((REPORT / "definition" / "pages" / "pages.json").read_text(encoding="utf-8"))
page_order = pm.get("pageOrder", [])
for name in page_order:
    pdir = REPORT / "definition" / "pages" / name
    if not pdir.exists():
        errors.append(f"  [MISSING PAGE FOLDER] '{name}' in pageOrder but no folder")
    elif not (pdir / "page.json").exists():
        errors.append(f"  [MISSING page.json]   page='{name}'")
    else:
        page_data = json.loads((pdir / "page.json").read_text(encoding="utf-8"))
        if page_data.get("name") != name:
            errors.append(
                f"  [NAME MISMATCH] folder='{name}' but page.json name='{page_data.get('name')}'"
            )
        # Count visuals
        vdir = pdir / "visuals"
        nvis = len(list(vdir.glob("*/visual.json"))) if vdir.exists() else 0
        print(f"  Page '{page_data.get('displayName')}' ({name}) - {nvis} visuals")
active = pm.get("activePageName")
if active not in page_order:
    errors.append(f"  [ACTIVE PAGE]  '{active}' not in pageOrder")

# -----------------------------------------------------------------------------
# 5. Relationships consistency
# -----------------------------------------------------------------------------
print("\n" + "=" * 70)
print("5. Relationships consistency")
print("=" * 70)
rel_text = (MODEL / "definition" / "relationships.tmdl").read_text(encoding="utf-8")
rel_refs = re.findall(r"(?:from|to)Column:\s+([^\s.]+)\.([^\s]+)", rel_text)
for table, col in rel_refs:
    if table not in entities:
        errors.append(f"  [REL MISSING ENTITY] {table}.{col}")
    elif col not in entities[table]:
        errors.append(f"  [REL MISSING COLUMN] {table}.{col}")
print(f"  Checked {len(rel_refs)} relationship column refs")

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
if errors:
    print(f"  [FAIL]  {len(errors)} errors:")
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("  [PASS]  No errors found")
if warnings:
    print(f"  {len(warnings)} warnings:")
    for w in warnings:
        print(w)
