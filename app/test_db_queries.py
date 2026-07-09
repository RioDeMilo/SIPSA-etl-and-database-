"""
test_db_queries.py — smoke-tests for db_queries.py
---------------------------------------------------
Run from any directory:
    python test_db_queries.py

On your server, point DB_PATH at your real agro.db before running.
"""

from pathlib import Path
import sys

# ── Point at whichever DB you want to test ────────────────────────────────────
TEST_DB = Path(__file__).resolve().parent / "agro_test.db"

# Allow overriding via command-line: python test_db_queries.py /path/to/agro.db
if len(sys.argv) > 1:
    TEST_DB = Path(sys.argv[1])

if not TEST_DB.exists():
    print(f"[ERROR] Database not found: {TEST_DB}")
    sys.exit(1)

# Import with patched path
import db_queries
db_queries.DB_PATH = TEST_DB  # override the module-level default

# ── Helper ────────────────────────────────────────────────────────────────────

PASS = "✅"
FAIL = "❌"
results = []

def check(label: str, condition: bool, detail: str = ""):
    icon = PASS if condition else FAIL
    msg = f"  {icon}  {label}"
    if detail:
        msg += f"  →  {detail}"
    print(msg)
    results.append(condition)

# ─────────────────────────────────────────────────────────────────────────────
print("\n══════════════════════════════════════════")
print("  AgroPrecios — DB Query Smoke Tests")
print(f"  DB: {TEST_DB}")
print("══════════════════════════════════════════\n")

# ── 0. Migration ──────────────────────────────────────────────────────────────
print("[ Migration ]")
try:
    db_queries.run_migrations(TEST_DB)
    # Run a second time to verify idempotency
    db_queries.run_migrations(TEST_DB)
    check("Migration runs without error", True)
except Exception as e:
    check("Migration runs without error", False, str(e))

# ── 1. get_all_cities() ───────────────────────────────────────────────────────
print("\n[ get_all_cities() ]")
cities = db_queries.get_all_cities(TEST_DB)

check("Returns a non-empty list",  len(cities) > 0,  f"{len(cities)} cities")
check("Each row has 'city_id'",    all("city_id"   in c for c in cities))
check("Each row has 'city_name'",  all("city_name" in c for c in cities))
check("city_id is an int",         isinstance(cities[0]["city_id"], int), str(type(cities[0]["city_id"])))
check("Sorted alphabetically",
      [c["city_name"] for c in cities] == sorted(c["city_name"] for c in cities))

print("\n  Cities found:")
for c in cities:
    print(f"    {c['city_id']:>3}  {c['city_name']}")

# Grab two city IDs for later tests
bogota_id   = next((c["city_id"] for c in cities if c["city_name"] == "Bogotá"),    None)
medellin_id = next((c["city_id"] for c in cities if c["city_name"] == "Medellín"),  None)
check("Bogotá found in cities",   bogota_id   is not None, f"id={bogota_id}")
check("Medellín found in cities", medellin_id is not None, f"id={medellin_id}")

# ── 2. get_all_products() ─────────────────────────────────────────────────────
print("\n[ get_all_products() ]")
products = db_queries.get_all_products(TEST_DB)

check("Returns a non-empty list",          len(products) > 0,  f"{len(products)} products")
check("Each row has 'product_id'",         all("product_id"         in p for p in products))
check("Each row has 'product_name'",       all("product_name"       in p for p in products))
check("Each row has 'is_converted_to_kg'", all("is_converted_to_kg" in p for p in products))
check("product_id is an int",              isinstance(products[0]["product_id"], int), str(type(products[0]["product_id"])))
check("is_converted_to_kg is 0 or 1",     all(p["is_converted_to_kg"] in (0, 1) for p in products))
check("Sorted alphabetically",
      [p["product_name"] for p in products] == sorted(p["product_name"] for p in products))

print("\n  Products found:")
for p in products:
    converted = "⚖️ converted" if p["is_converted_to_kg"] else ""
    print(f"    {p['product_id']:>5}  {p['product_name']:<35} {converted}")

# Grab two product IDs for later tests
coco_id   = next((p["product_id"] for p in products if p["product_name"] == "Coco"),    None)
lulo_id = next((p["product_id"] for p in products if p["product_name"] == "Lulo"),   None)
check("Coco found",   coco_id   is not None, f"id={coco_id}")
check("Lulo found",  lulo_id is not None, f"id={lulo_id}")

# ── 3. get_latest_price() ─────────────────────────────────────────────────────
print("\n[ get_latest_price() — happy paths ]")

# Test pair A: Bogotá + Coco (two rows seeded — should get newest)
if bogota_id and coco_id:
    row = db_queries.get_latest_price(bogota_id, coco_id, TEST_DB)
    check("Returns a result for Bogotá / Coco", row is not None, str(row))
    if row:
        check("price_kilo is a float",    isinstance(row["price_kilo"], float), str(row["price_kilo"]))
        check("price_kilo is 1900.0 (latest row)", row["price_kilo"] == 1900.0, str(row["price_kilo"]))
        check("city_name is Bogotá",      row["city_name"] == "Bogotá",        row["city_name"])
        check("product_name is coco", row["product_name"] == "Coco", row["product_name"])
        check("All expected keys present",
              all(k in row for k in ("price_id","product_id","product_name","city_id","city_name","price_kilo","price_date","is_converted_to_kg")))
        print(f"\n  Bogotá / Coco result:")
        for k, v in row.items():
            print(f"    {k:<25} {v}")

# Test pair B: Medellín + Lulo
print()
if medellin_id and lulo_id:
    row = db_queries.get_latest_price(medellin_id, lulo_id, TEST_DB)
    check("Returns a result for Medellín / Lulo", row is not None, str(row))
    if row:
        check("price_kilo is 3100.0 (latest row)", row["price_kilo"] == 3100.0, str(row["price_kilo"]))
        print(f"\n  Medellín / Lulo result:")
        for k, v in row.items():
            print(f"    {k:<25} {v}")

# ── 4. get_latest_price() — edge cases ────────────────────────────────────────
print("\n[ get_latest_price() — edge cases ]")

no_data = db_queries.get_latest_price(9999, 9999, TEST_DB)
check("Returns None for unknown city/product pair", no_data is None, str(no_data))

# ── Summary ───────────────────────────────────────────────────────────────────
passed = sum(results)
total  = len(results)
print(f"\n══════════════════════════════════════════")
print(f"  Results: {passed}/{total} checks passed")
if passed == total:
    print("  🎉  All good — Step 3 complete!")
else:
    print(f"  ⚠️   {total - passed} check(s) failed — review output above.")
print("══════════════════════════════════════════\n")
