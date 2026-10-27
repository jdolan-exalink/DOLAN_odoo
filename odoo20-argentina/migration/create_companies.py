import json, os, sys

def _p(name):
    for base in ("/tmp/migration/data", "/tmp/migration", "data"):
        p = os.path.join(base, name)
        if os.path.exists(p):
            return p
    raise SystemExit("no se encontro: " + name)

CT = env["account.chart.template"]  # noqa: F821 (odoo shell)
mapping = CT._get_chart_template_mapping(get_all=True)
ar_code = next((k for k, v in mapping.items() if v.get("module") == "l10n_ar"), None)
if not ar_code:
    print("FALLO: no se encontro template code para l10n_ar. keys:",
          list(mapping)[:20])
    sys.exit(1)
print("template code AR:", ar_code)

CTX = json.load(open(_p("company_context.json")))
RESP = {"Responsable Inscripto": "l10n_ar.res_IVARI", "Monotributo": "l10n_ar.res_MON_Ind"}
ARS = env.ref("base.ARS")
AR = env.ref("base.ar")
companies = []
for entity in ("1", "2", "3"):
    ctx = CTX[entity]
    vat = ctx["cuit"].replace("-", "")
    co = env["res.company"].create({
        "name": ctx["name"],
        "currency_id": ARS.id,
        "country_id": AR.id,
        "vat": vat,
        "l10n_ar_afip_responsibility_type_id": env.ref(RESP[ctx["condicion_iva"]]).id,
    })
    CT.try_loading(ar_code, co)
    companies.append(co)
    print(f"empresa creada: [{co.id}] {co.name} vat={co.vat} "
          f"resp={co.l10n_ar_afip_responsibility_type_id.code}")

# el usuario del shell (admin) gestiona las tres
env.user.company_ids |= env["res.company"].browse([c.id for c in companies])

for co in companies:
    journals = env["account.journal"].search([("company_id", "=", co.id)])
    print(f"check [{co.name}] journals={len(journals)} chart={co.chart_template or '-'}")

env.cr.commit()
print("COMMIT OK")
