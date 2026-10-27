import collections
import json

BASE = "/tmp/migration/data"
CO_BY_ENTITY = {1: "DOLAN SS", 2: "JUAN MARTIN DOLAN", 3: "CINTIA VERONICA GOROSITO"}

products = json.load(open(BASE + "/products.json", encoding="utf-8"))
Company = env["res.company"]  # noqa: F821
Product = env["product.template"]
co_by_name = {c.name: c for c in Company.search([])}
companies = {ent: co_by_name[name] for ent, name in CO_BY_ENTITY.items()}

def sale_tax(company, amount):
    if not amount:
        return False
    t = env["account.tax"].search([
        ("type_tax_use", "=", "sale"),
        ("amount", "=", float(amount)),
        ("company_id", "=", company.id),
    ], limit=1)
    return t.id if t else False

created = {}
by_co = collections.Counter()
taxes = collections.Counter()
for p in products:
    co = companies[int(p["entity"])]
    price = p.get("price") or 0
    tva = float(p.get("tva_tx") or 0)
    vals = {
        "name": (p.get("label") or "").strip() or "SIN NOMBRE",
        "default_code": p.get("ref") or False,
        "list_price": float(price) if price else 0.0,
        "company_id": co.id,
        "active": (str(p.get("statut")) == "1"),
        "taxes_id": [(6, 0, [x for x in [sale_tax(co, tva)] if x])],
    }
    if p.get("description"):
        vals["description"] = p["description"]
    if p.get("barcode"):
        vals["barcode"] = p["barcode"]
    tpl = Product.create(vals)
    created[p["rowid"]] = tpl.id
    by_co[co.name] += 1
    taxes[str(tva)] += 1

with open("/tmp/product_map.json", "w") as fh:
    json.dump(created, fh)

src = collections.Counter(CO_BY_ENTITY[int(p["entity"])] for p in products)
print("por empresa:", dict(by_co))
print("fuente:", dict(src))
print("impuestos aplicados (tva_tx->n):", dict(taxes))
assert dict(by_co) == dict(src), "contados != fuente"
env.cr.commit()
print("COMMIT OK")
