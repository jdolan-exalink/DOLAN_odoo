Lang = env["res.lang"].sudo().with_context(active_test=False)
lang = Lang.search([("code", "=", "es_AR")], limit=1)
if not lang:
    lang = Lang._create_lang("es_AR")
    print("lang creado:", lang.code, "active", lang.active)
elif not lang.active:
    lang.action_unarchive()
    print("lang reactivado:", lang.code, "active", lang.active)
else:
    print("lang ya activo:", lang.code)
print("date_format:", lang.date_format, "| time_format:", lang.time_format)

env["ir.default"].sudo().set("res.partner", "lang", "es_AR", company_id=False)
print("ir.default res.partner.lang = es_AR")

U = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
n = 0
for u in U.search([]):
    if u.partner_id and u.partner_id.lang != "es_AR":
        u.partner_id.lang = "es_AR"
        n += 1
for co in env["res.company"].sudo().browse([5, 6, 7]):  # noqa: F821
    if co.partner_id.lang != "es_AR":
        co.partner_id.lang = "es_AR"
        n += 1
print("partners actualizados a es_AR:", n)
env.cr.commit()
print("COMMIT OK")
