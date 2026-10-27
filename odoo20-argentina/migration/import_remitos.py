import json
import os
import sys
from datetime import datetime

BASE = "/tmp/migration/data"
load = lambda n: json.load(open(os.path.join(BASE, n), encoding="utf-8"))  # noqa: E731
expeds = load("expeditions.json")
elns = load("expedition_lines.json")
partner_map = {int(k): v for k, v in json.load(open("/tmp/partner_map.json")).items()}
MAP_PATH = "/tmp/remito_map.json"
remito_map = json.load(open(MAP_PATH)) if os.path.exists(MAP_PATH) else {}
limit = int(os.environ.get("REMITO_LIMIT", "0"))

lines_by_exp = {}
for l in elns:
    lines_by_exp.setdefault(l["fk_expedition"], []).append(l)

Company = env["res.company"]  # noqa: F821
PT = env["stock.picking.type"]
Product = env["product.template"
             ] if False else env["product.template"]
stats = []
errors = []

def synth_product(co):
    p = env["product.template"].search(
        [("default_code", "=", "REMITO-IMPORT"), ("company_id", "=", co.id)], limit=1)
    if not p:
        p = env["product.template"].create({
            "name": "Mercadería según remito (importado)",
            "default_code": "REMITO-IMPORT",
            "type": "consu",
            "sale_ok": False,
            "purchase_ok": False,
            "company_id": co.id,
        })
    return p

for e in expeds:
    rid = e["rowid"]
    if str(rid) in remito_map:
        stats.append(("skip", e["ref"]))
        continue
    if limit and len([s for s in stats if s[0] == "alta"]) >= limit:
        break
    try:
        co = Company.browse(5)  # DOLAN SS: todas las expeditions son entity 1
        incoming = (e["ref"] or "").startswith("REM/IN/")
        ptype = PT.search([("company_id", "=", co.id),
                           ("code", "=", "incoming" if incoming else "outgoing")], limit=1)
        if not ptype:
            raise SystemExit("sin picking type para empresa " + str(co.id))
        date_src = e.get("date_expedition") or e.get("date_valid") or e.get("date_creation")
        when = datetime.strptime(date_src[:19], "%Y-%m-%d %H:%M:%S") if date_src else None
        picking = env["stock.picking"].create({
            "partner_id": partner_map[e["fk_soc"]],
            "picking_type_id": ptype.id,
            "location_id": ptype.default_location_src_id.id,
            "location_dest_id": ptype.default_location_dest_id.id,
            "origin": e["ref"],
            **({"scheduled_date": when} if when else {}),
        })
        prod = synth_product(co)
        nlines = 0
        for l in lines_by_exp.get(rid, []):
            qty = float(l.get("qty") or 1)
            texto = (l.get("description") or e["ref"] or "Remito")[:2000]
            mv = env["stock.move"].create({
                "picking_id": picking.id,
                "company_id": co.id,
                "description_picking": texto,
                "description_picking_manual": texto,
                "product_id": prod.product_variant_id.id,
                "product_uom_qty": qty,
                "quantity": qty,
                "picked": True,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
            })
            nlines += 1
        if lines_by_exp.get(rid):
            picking.note = (lines_by_exp[rid][0].get("description") or "")[:2000] or False
        picking._action_done()
        picking.invalidate_recordset()
        # numeracion oficial del remito + fecha de emision historica
        picking.name = e["ref"]
        if when:
            picking.date_done = when
        remito_map[str(rid)] = picking.id
        stats.append(("alta", e["ref"], picking.name, picking.state, nlines))
    except Exception as ex:
        errors.append({"ref": e["ref"], "err": f"{type(ex).__name__}: {ex}"[:220]})

json.dump(remito_map, open(MAP_PATH, "w"))
print("altas:", len([s for s in stats if s[0] == "alta"]), "| skips:", len([s for s in stats if s[0] == "skip"]))
for s in stats:
    if s[0] == "alta":
        print("  OK", s[1], "->", s[2], "| state:", s[3], "| lineas:", s[4])
print("errores:", len(errors))
for er in errors:
    print("  ERR", er)
if errors:
    sys.exit(2)
env.cr.commit()
print("COMMIT OK")
