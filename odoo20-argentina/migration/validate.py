import collections
import json
import os

BASE = "/tmp/migration/data"
load = lambda n: json.load(open(os.path.join(BASE, n), encoding="utf-8"))  # noqa: E731
invoices = load("invoices.json")
pmap = {int(k): v for k, v in json.load(open("/tmp/partner_map.json")).items()}
imap = {int(k): v for k, v in json.load(open("/tmp/invoice_map.json")).items()}

report = {
    "fuente": len(invoices),
    "mapa": len(imap),
    "faltan_en_mapa": [r["ref"] for r in invoices if r["rowid"] not in imap],
    "sobra_en_mapa": [k for k in imap if k not in {r["rowid"] for r in invoices}],
}
Move = env["account.move"]  # noqa: F821
moves = Move.browse(list(imap.values()))

report["por_estado"] = dict(collections.Counter(m.state for m in moves))
report["por_pago"] = dict(collections.Counter(m.payment_state for m in moves))
report["por_tipo"] = dict(collections.Counter(m.move_type for m in moves))
report["por_empresa"] = dict(collections.Counter(m.company_id.name for m in moves))
report["sin_cae"] = [m.ref for m in moves if not m.l10n_ar_fiscal_auth_code]

by_id = {r["rowid"]: r for r in invoices}
bad_totals, bad_cae, bad_docnum = [], [], []
for rid, mid in imap.items():
    src = by_id[rid]
    m = Move.browse(mid)
    if abs(abs(m.amount_total) - abs(float(src["total_ttc"] or 0))) > 0.02:
        bad_totals.append({"ref": src["ref"], "odoo": round(m.amount_total, 2),
                           "src": float(src["total_ttc"] or 0),
                           "src_tva": float(src["total_tva"] or 0)})
    if (m.l10n_ar_fiscal_auth_code or "") != (src["arca_cae"] or ""):
        bad_cae.append(src["ref"])
    # formato oficial latam: name == ref de origen (prefijo doc_code_prefix + PV5-NUM8)
    if m.name != (src["ref"] or ""):
        bad_docnum.append({"ref": src["ref"], "odoo": m.name, "src": src["ref"]})
    elif m.l10n_latam_document_number != (src["ref"] or "").split(" ", 1)[-1]:
        bad_docnum.append({"ref": src["ref"], "odoo": m.l10n_latam_document_number,
                           "src": (src["ref"] or "").split(" ", 1)[-1]})

report["totales_desviados"] = len(bad_totals)
report["cae_distintos"] = bad_cae
report["num_doc_desviados"] = bad_docnum[:10]
print(json.dumps(report, indent=1, ensure_ascii=False))
for b in bad_totals:
    print("BAD_TOTAL", b)
print("CHECK_DONE")
