import json
import os
import sys
from datetime import datetime

BASE = "/tmp/migration/data"
load = lambda n: json.load(open(os.path.join(BASE, n), encoding="utf-8"))  # noqa: E731
bills = [b for b in load("bills.json")] if os.path.exists(os.path.join(BASE, "bills.json")) else []
partner_map = {int(k): v for k, v in json.load(open("/tmp/partner_map.json")).items()}
MAP_PATH = "/tmp/bill_map.json"
bill_map = json.load(open(MAP_PATH)) if os.path.exists(MAP_PATH) else {}
# saneo: ids del mapa que no sobrevivieron en la DB (rollback) se re-importan
if bill_map:
    _alive = {k: v for k, v in bill_map.items() if env["account.move"].browse(v).exists()}
    if len(_alive) != len(bill_map):
        print("mapa saneado:", len(bill_map), "->", len(_alive))
    bill_map = _alive
limit = int(os.environ.get("BILL_LIMIT", "0"))

Move = env["account.move"]  # noqa: F821
CO_ID = 5  # todos los comprobantes recibidos son entity 1 (DOLAN SS)
co = env["res.company"].browse(CO_ID)
journal = env["account.journal"].search(
    [("company_id", "=", CO_ID), ("type", "=", "purchase")], limit=1)
expense = env["account.account"].with_company(co).search(
    [("account_type", "=", "expense")], order="code", limit=1)
doc_types = {d.code: d for d in env["l10n_latam.document.type"].search(
    [("country_id", "=", env.ref("base.ar").id), ("active", "=", True)])}

def purchase_tax(amount):
    # RI: toda linea de factura de compra necesita UN impuesto del grupo VAT;
    # en cero se usa el "VAT 0%" (grupo VAT) en vez de nada
    if not amount:
        # RI comprando a monotributo (Fact C): Odoo exige "VAT Not Applicable"
        t0 = env["account.tax"].search([
            ("type_tax_use", "=", "purchase"), ("amount", "=", 0),
            ("company_id", "=", CO_ID),
            ("tax_group_id.name", "ilike", "Not Applicable")], limit=1)
        if not t0:
            t0 = env["account.tax"].search([
                ("type_tax_use", "=", "purchase"), ("amount", "=", 0),
                ("company_id", "=", CO_ID)], limit=1)
        return t0.id if t0 else False
    t = env["account.tax"].search([
        ("type_tax_use", "=", "purchase"), ("amount", "=", float(amount)),
        ("company_id", "=", CO_ID)], limit=1)
    return t.id if t else False

RATES = (0.0, 10.5, 21.0, 27.0, 5.0)
def line_rate(ln):
    ht = float(ln.get("total_ht") or 0)
    # det de compras guarda el IVA en "tva" (no existe total_tva)
    tva = float(ln.get("tva") if ln.get("tva") is not None else (ln.get("total_tva") or 0))
    if not ht:
        return float(ln.get("tva_tx") or 0) if tva else 0.0
    rate = round(abs(tva / ht) * 100, 2)
    for cand in RATES:
        if abs(rate - cand) < 0.05:
            return cand
    return float(ln.get("tva_tx") or 0)

# lineas por bill (solo las de bills reales)
lines_by_bill = {}
for ln in load("bill_lines.json"):
    lines_by_bill.setdefault(ln["fk_facture_fourn"], []).append(ln)

stats, errors, mismatches = [], [], []
for b in bills:
    rid = b["rowid"]
    if str(rid) in bill_map:
        stats.append(("skip", b["ref"]))
        continue
    # placeholders "(PROVx)" en cero: artefactos de la import custom, sin lineas
    if float(b.get("total_ttc") or 0) == 0 or (b.get("ref") or "").startswith("(PROV"):
        stats.append(("excluido", b["ref"]))
        continue
    if limit and len([s for s in stats if s[0] == "alta"]) >= limit:
        break
    try:
        doc_code, doc_num = (b.get("ref_supplier") or "").split(" ", 1)
        doc = doc_types.get(doc_code)
        if not doc:
            raise SystemExit("doc type? " + str(b.get("ref_supplier")))
        date = b.get("datef") or b.get("date_valid")
        line_ids = []
        for ln in lines_by_bill.get(rid, []):
            qty = float(ln.get("qty") or 1)
            disc = float(ln.get("remise_percent") or 0)
            price = ln.get("pu_ht") if ln.get("pu_ht") not in (None, "") else ln.get("price")
            line_ids.append((0, 0, {
                "name": (ln.get("description") or b["ref"])[:2000],
                "quantity": qty,
                "price_unit": float(price or 0),
                "discount": disc,
                "account_id": expense.id,
                "tax_ids": [(6, 0, [x for x in [purchase_tax(line_rate(ln))] if x])],
            }))
        if not line_ids:
            raise SystemExit("bill sin lineas: " + b["ref"])
        mv = Move.create({
            "company_id": CO_ID,
            "partner_id": partner_map[b["fk_soc"]],
            "move_type": "in_invoice",
            "journal_id": journal.id,
            "invoice_date": date,
            "date": date,
            "l10n_latam_document_type_id": doc.id,
            "l10n_latam_document_number": doc_num,
            "ref": b.get("ref") or False,
            "narration": b.get("note_public") or False,
            "line_ids": line_ids,
        })
        mv.action_post()
        bill_map[str(rid)] = mv.id
        stats.append(("alta", b["ref"], mv.name, mv.amount_total))
        diff = abs(mv.amount_total - float(b["total_ttc"] or 0))
        if diff > 0.02:
            mismatches.append({"ref": b["ref"], "odoo": round(mv.amount_total, 2),
                               "dolibarr": float(b["total_ttc"] or 0)})
    except Exception as error:
        errors.append({"ref": b.get("ref"), "err": f"{type(error).__name__}: {error}"[:260]})

json.dump(bill_map, open(MAP_PATH, "w"))
print("altas:", len([s for s in stats if s[0] == "alta"]), "| skips:", len([s for s in stats if s[0] == "skip"]), "| excluidos:", len([s for s in stats if s[0] == "excluido"]))
for s in stats:
    if s[0] == "alta":
        print("  OK", s[1], "->", s[2], "| total", s[3])
print("errores:", len(errors))
for e in errors[:6]:
    print("  ERR", e)
print("mismatches:", mismatches)
if errors:
    sys.exit(2)
env.cr.commit()
print("COMMIT OK")
