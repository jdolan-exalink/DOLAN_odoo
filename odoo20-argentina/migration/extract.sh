#!/bin/bash
set -euo pipefail
# Extract Dolibarr source tables to normalized JSON for the Odoo migration.
# READ-ONLY on the dolibarr database. Secrets never printed.
# v2: server-side JSON_ARRAYAGG (TSV broke on embedded newlines in text fields).

BASE="$(cd "$(dirname "$0")" && pwd)"
DATA="$BASE/data"
mkdir -p "$DATA"

set -a; . /root/dolibarr/.env; set +a

q() {
  docker exec -i dolibarr_mariadb mariadb -u"$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" \
    --batch --raw -N -e "$1"
}

echo "Exportando a JSON (JSON_ARRAYAGG del servidor)..."
python3 - "$DATA" <<'PY'
import json, subprocess, sys, os
data = sys.argv[1]
env = dict(os.environ)
tables = {
    "llx_societe": "societes",
    "llx_facture": "invoices",
    "llx_facturedet": "invoice_lines",
    "llx_product": "products",
    "llx_paiement": "payments",
    "llx_c_country": "countries",
    "llx_societe_extrafields": "societe_extrafields",
    "llx_expedition": "expeditions",
    "llx_expeditiondet": "expedition_lines",
    "llx_facture_fourn": "bills",
    "llx_facture_fourn_det": "bill_lines",
}
def run(sql):
    r = subprocess.run(
        ["docker", "exec", "-i", "dolibarr_mariadb", "mariadb",
         "-u" + env["DB_USER"], "-p" + env["DB_PASSWORD"], env["DB_NAME"],
         "--default-character-set=utf8mb4",
         "--batch", "--raw", "-N", "-e", sql],
        capture_output=True)
    if r.returncode != 0:
        raise SystemExit("SQL error: " + r.stderr.decode("utf-8", "replace").strip()[:300])
    return r.stdout.decode("utf-8", "replace").strip()
for table, name in tables.items():
    cols = run(f"SELECT column_name FROM information_schema.columns "
               f"WHERE table_schema=DATABASE() AND table_name='{table}' ORDER BY ordinal_position;")
    col_list = [c for c in cols.splitlines()
                if c not in {"geopoint"}]  # geopoint: bytes invalidos rompen JSON_ARRAYAGG (bug server)
    objs = ", ".join(f"'{c}', `{c}`" for c in col_list)
    sel = ", ".join(f"`{c}`" for c in col_list)
    rows = []
    last = 0
    while True:
        raw = run(
            f"SELECT JSON_VALID(j), j FROM (SELECT COALESCE(JSON_ARRAYAGG(JSON_OBJECT({objs})), '[]') j FROM "
            f"(SELECT {sel} FROM {table} WHERE rowid > {last} ORDER BY rowid LIMIT 200) s) x;")
        line = raw.split("\t", 1)
        if line[0] != "1":
            raise SystemExit(f"JSON_INVALID server-side in {table} chunk after rowid {last}")
        chunk = json.loads(line[1])
        if not chunk:
            break
        rows.extend(chunk)
        last = chunk[-1].get("rowid", last)
        if len(chunk) < 200:
            break
    with open(os.path.join(data, name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(rows, fh, ensure_ascii=False)
    print(f"  {name}: {len(rows)} filas")
PY

cat > "$DATA/company_context.json" <<'JSON'
{
  "1": {"name": "DOLAN SS", "cuit": "30-71903035-8", "condicion_iva": "Responsable Inscripto", "pv": 1},
  "2": {"name": "JUAN MARTIN DOLAN", "cuit": "20-26694600-8", "condicion_iva": "Monotributo", "pv": 8},
  "3": {"name": "CINTIA VERONICA GOROSITO", "cuit": "27-34563638-8", "condicion_iva": "Monotributo", "pv": 4}
}
JSON

echo "Manifiesto..."
python3 - "$DATA" <<'PY'
import json, os, sys, collections
data = sys.argv[1]
def load(n): return json.load(open(os.path.join(data, n), encoding="utf-8"))
soc, inv, det = load("societes.json"), load("invoices.json"), load("invoice_lines.json")
man = {
  "counts": {"societes": len(soc), "invoices": len(inv), "invoice_lines": len(det),
             "products": len(load("products.json")), "payments": len(load("payments.json"))},
  "societes_by_entity": dict(collections.Counter(r["entity"] for r in soc)),
  "invoices_by_entity": dict(collections.Counter(r["entity"] for r in inv)),
  "invoices_by_type_status": dict(collections.Counter(f"t{r['type']}_s{r['fk_statut']}" for r in inv)),
  "tva_tx_values": dict(collections.Counter(r["tva_tx"] for r in det)),
}
for e in ("1", "2", "3"):
    rows = [r for r in inv if r["entity"] == e]
    man[f"entity_{e}"] = {
      "invoices": len(rows),
      "total_ttc": round(sum(float(r["total_ttc"] or 0) for r in rows), 2),
      "total_tva": round(sum(float(r["total_tva"] or 0) for r in rows), 2),
    }
dates = sorted(r["datef"] for r in inv if r["datef"])
man["datef_range"] = [dates[0], dates[-1]] if dates else None
json.dump(man, open(os.path.join(data, "manifest.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps(man["counts"]))
print("entities inv:", man["invoices_by_entity"], "| types:", man["invoices_by_type_status"])
PY
echo "OK: $DATA"
