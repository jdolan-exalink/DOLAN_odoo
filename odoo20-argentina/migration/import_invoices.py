import collections
import json
import os
import re
from datetime import date

BASE = "/tmp/migration/data"
CO_BY_ENTITY = {1: "DOLAN SS", 2: "JUAN MARTIN DOLAN", 3: "CINTIA VERONICA GOROSITO"}
DOCMAP = {"1": "01", "2": "02", "3": "03", "6": "06", "7": "07", "8": "08",
          "11": "11", "12": "12", "13": "13"}  # fallback zero-pad si no

def load(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as fh:
        return json.load(fh)

invoices = load("invoices.json")
lines_by_inv = collections.defaultdict(list)
for ln in load("invoice_lines.json"):
    lines_by_inv[ln["fk_facture"]].append(ln)
societes = {str(r["rowid"]): r for r in load("societes.json")}
src_products = {str(r["rowid"]): r for r in load("products.json")}
partner_map = {int(k): v for k, v in json.load(open("/tmp/partner_map.json")) .items()}
product_map = {int(k): v for k, v in json.load(open("/tmp/product_map.json")).items()}

MAP_PATH = "/tmp/invoice_map.json"
if os.path.exists(MAP_PATH):
    invoice_map = json.load(open(MAP_PATH))
else:
    invoice_map = {}

Move = env["account.move"]  # noqa: F821
Company = env["res.company"]
co_by_name = {c.name: c for c in Company.search([])}
companies = {ent: co_by_name[name] for ent, name in CO_BY_ENTITY.items()}

setup = {}
for ent, co in companies.items():
    sale_journal = env["account.journal"].search(
        [("company_id", "=", co.id), ("type", "=", "sale")], limit=1)
    pay_journal = env["account.journal"].search(
        [("company_id", "=", co.id), ("type", "=", "bank")], limit=1)
    if not sale_journal or not pay_journal:
        raise SystemExit(f"falta journal en {co.name}")
    income = env["account.account"].with_company(co).search(
        [("account_type", "=", "income")], order="code", limit=1)
    income_by_code = {a.code: a for a in env["account.account"].with_company(co).search(
        [("account_type", "=", "income")])}
    doc_types = {d.code: d for d in env["l10n_latam.document.type"].search(
        [("country_id", "=", env.ref("base.ar").id), ("active", "=", True)])}
    setup[ent] = dict(co=co, sale=sale_journal, pay=pay_journal,
                      income=income, income_by_code=income_by_code, doc_types=doc_types)

def sale_tax(co, amount):
    if not amount:
        return False
    t = env["account.tax"].search([
        ("type_tax_use", "=", "sale"), ("amount", "=", float(amount)),
        ("company_id", "=", co.id)], limit=1)
    return t.id if t else False

def doc_number(src):
    pv, nro = src.get("arca_pv"), src.get("arca_cbte_nro")
    if pv and nro:
        return f"{int(pv):04d}-{int(nro):08d}"
    m = re.search(r"(\d{4,5})-(\d{6,8})$", src.get("ref") or "")
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):08d}"
    raise SystemExit("sin numero ARCA: ref=" + str(src.get("ref")))

def income_for(ent, src_line, product):
    s = setup[ent]
    if product and product.get("accountancy_code_sell"):
        acc = s["income_by_code"].get(str(product["accountancy_code_sell"]))
        if acc:
            return acc.id
    return s["income"].id

stats = collections.Counter()
mismatches = []
order = sorted(invoices, key=lambda r: (r.get("datef") or "", r.get("ref") or ""))
for src in order:
    rid = src["rowid"]
    if str(rid) in invoice_map:
        stats["skip_existente"] += 1
        continue
    ent = int(src["entity"])
    s = setup[ent]
    co = s["co"]
    inv_date = src.get("datef") or src.get("date_valid")
    if not inv_date:
        raise SystemExit(f"factura {src['ref']} sin fecha")
    cbte = str(src["arca_cbte_tipo"])
    doc = s["doc_types"].get(cbte) or s["doc_types"].get(DOCMAP.get(cbte, ""))
    if not doc:
        raise SystemExit(f"doc type no encontrado: {cbte}")
    # verdad fiscal = familia ARCA emitida; v23 usa type 1 y 2 para NC
    mv_type = "out_refund" if doc.internal_type == "credit_note" else "out_invoice"
    neg = mv_type == "out_refund" and float(src.get("total_ht") or 0) < 0

    line_ids = []
    # verdad por línea: total_tva/total_ht de la fuente (la cabecera fiscal
    # coincide con la suma); tva_tx es a veces inconsistente (21 donde hubo 10.5)
    RATES = (0.0, 10.5, 21.0, 27.0, 5.0, 2.5, 42.0, 1.5, 3.0)
    def line_rate(ln):
        ht = float(ln.get("total_ht") or 0)
        tva = float(ln.get("total_tva") or 0)
        if not ht:
            return float(ln.get("tva_tx") or 0) if tva else 0.0
        rate = round(abs(tva / ht) * 100, 2)
        for cand in RATES:
            if abs(rate - cand) < 0.05:
                return cand
        return float(ln.get("tva_tx") or 0)
    for ln in lines_by_inv.get(rid, []):
        prod_src = src_products.get(str(ln.get("fk_product") or ""))
        pid = product_map.get(ln.get("fk_product"))
        qty = float(ln.get("qty") or 1)
        disc = float(ln.get("remise_percent") or 0)
        price = ln.get("price")
        if price in (None, "", 0) and float(ln.get("total_ht") or 0):
            # price nulo con total_ht>0 (v23): derivar unidad desde el neto
            net = float(ln["total_ht"]) / qty
            price = net / (1 - disc / 100) if disc < 100 else net
        if neg:
            price = abs(float(price or 0)) or price
        vals = {
            "name": (ln.get("label") or ln.get("description") or "").strip() or "Linea",
            "quantity": qty,
            "price_unit": float(price or 0),
            "discount": disc,
            "account_id": income_for(ent, prod_src, prod_src),
            "tax_ids": [(6, 0, [x for x in [sale_tax(co, line_rate(ln))] if x])],
        }
        if pid:
            vals["product_id"] = pid
        line_ids.append((0, 0, vals))

    mv = Move.create({
        "company_id": co.id,
        "partner_id": partner_map[src["fk_soc"]],
        "move_type": mv_type,
        "journal_id": s["sale"].id,
        "invoice_date": inv_date,
        "date": inv_date,
        "l10n_latam_document_type_id": doc.id,
        "l10n_latam_document_number": doc_number(src),
        "ref": src.get("ref") or False,
        "narration": src.get("note_public") or False,
        "line_ids": line_ids,
    })
    mv.action_post()

    # CAE real post-posting (los journals no tienen fiscal_ws -> post limpio)
    mv.sudo().write({
        "l10n_ar_fiscal_auth_code": src["arca_cae"],
        "l10n_ar_fiscal_auth_code_due": src.get("arca_cae_vto") or False,
        "l10n_ar_fiscal_auth_mode": "CAE",
        "l10n_ar_fiscal_result": "A",
    })

    # pago total => paid
    print("pay:", src["ref"])
    wiz = env["account.payment.register"].with_context(
        active_model="account.move", active_ids=[mv.id]
    ).create({"payment_date": inv_date, "journal_id": s["pay"].id})
    wiz._create_payments()

    invoice_map[str(rid)] = mv.id
    stats["importadas"] += 1
    src_total = float(src["total_ttc"] or 0)
    diff = abs(mv.amount_total - src_total)
    if diff > 0.02:
        mismatches.append({"ref": src["ref"], "odoo": round(mv.amount_total, 2),
                           "dolibarr": src_total, "diff": round(diff, 2)})
    if stats["importadas"] % 20 == 0:
        env.cr.commit()
        json.dump(invoice_map, open(MAP_PATH, "w"))
        print("...progreso:", stats["importadas"])

json.dump(invoice_map, open(MAP_PATH, "w"))
print("stats:", dict(stats))
print("mismatches_totales:", len(mismatches))
for m in mismatches[:10]:
    print("  MISMATCH", m)
env.cr.commit()
print("COMMIT OK")
