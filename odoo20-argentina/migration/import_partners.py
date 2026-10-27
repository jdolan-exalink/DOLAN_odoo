import collections
import json
import os
import re

BASE = "/tmp/migration/data"
CO_BY_ENTITY = {1: "DOLAN SS", 2: "JUAN MARTIN DOLAN", 3: "CINTIA VERONICA GOROSITO"}
RESP = {"RI": "l10n_ar.res_IVARI", "MO": "l10n_ar.res_RM"}

def load(name):
    with open(os.path.join(BASE, name), encoding="utf-8") as fh:
        return json.load(fh)

societes = load("societes.json")
extras = {r["fk_object"]: r for r in load("societe_extrafields.json")}
countries = load("countries.json")
country_by_id = {r["rowid"]: r for r in countries}

Company = env["res.company"]  # noqa: F821
Partner = env["res.partner"]
co_by_name = {c.name: c for c in Company.search([])}
companies = {}
for ent, name in CO_BY_ENTITY.items():
    if name not in co_by_name:
        raise SystemExit("falta empresa: " + name)
    companies[ent] = co_by_name[name]

def country_id(fk):
    row = country_by_id.get(fk)
    iso = (row or {}).get("iso") or ""
    if not iso:
        return False
    c = env["res.country"].search([("code", "=", iso.upper())], limit=1)
    return c.id if c else False

CUIT = re.compile(r"^[23]\d{9}$")
created = {}
stats = collections.Counter()
by_co = collections.Counter()

for s in societes:
    co = companies[s["entity"]]
    vat_digits = re.sub(r"\D", "", s.get("siren") or "")
    vals = {
        "name": (s.get("nom") or "").strip() or (s.get("name_alias") or "SIN NOMBRE"),
        "company_id": co.id,
        "street": s.get("address") or False,
        "zip": s.get("zip") or False,
        "city": s.get("town") or False,
        "country_id": country_id(s.get("fk_pays")),
        "phone": (s.get("phone_mobile") or s.get("phone") or False),
        "email": s.get("email") or False,
        "customer_rank": 1 if (s.get("client") or "0") not in ("0", "", None) else 0,
        "supplier_rank": 1 if (s.get("fournisseur") or "0") not in ("0", "", None) else 0,
        "ref": s.get("code_client") or False,
    }
    if CUIT.match(vat_digits):
        vals["vat"] = vat_digits
    ex = extras.get(s["rowid"])
    if ex:
        resp = RESP.get((ex.get("condicion_iva") or "").strip().upper())
        if resp:
            vals["l10n_ar_afip_responsibility_type_id"] = env.ref(resp).id
    p = Partner.create(vals)
    created[s["rowid"]] = p.id
    stats["created"] += 1
    if vals.get("vat"):
        stats["con_cuit"] += 1
    if ex:
        stats["con_extrafields"] += 1
    by_co[co.name] += 1

with open("/tmp/partner_map.json", "w") as fh:
    json.dump(created, fh)

print("stats:", dict(stats))
print("por empresa:", dict(by_co))
esperado = {"DOLAN SS": 807, "JUAN MARTIN DOLAN": 793, "CINTIA VERONICA GOROSITO": 794}
print("esperado:", esperado)
assert dict(by_co) == esperado, "contados != esperado"
env.cr.commit()
print("COMMIT OK")
