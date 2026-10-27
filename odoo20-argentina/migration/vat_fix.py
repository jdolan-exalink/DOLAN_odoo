import json, re
societes = {str(r["rowid"]): r for r in json.load(open("/tmp/migration/data/societes.json"))}
pmap = json.load(open("/tmp/partner_map.json"))
CUIT = re.compile(r"^[23]\d{10}$")
Partner = env["res.partner"]  # noqa: F821
n = 0
for srid, pid in pmap.items():
    s = societes.get(srid)
    if not s:
        continue
    digits = re.sub(r"\D", "", s.get("siren") or "")
    if CUIT.match(digits):
        Partner.browse(pid).vat = digits
        n += 1
print("vats escritos:", n)
env.cr.commit()
print("COMMIT OK")
