resp = env.ref("l10n_ar.res_RM")  # noqa: F821
for name in ("JUAN MARTIN DOLAN", "CINTIA VERONICA GOROSITO"):
    co = env["res.company"].search([("name", "=", name)])
    co.partner_id.l10n_ar_afip_responsibility_type_id = resp
    print(f"[{name}] -> {resp.name} (code {resp.code})")
co = env["res.company"].search([("name", "=", "DOLAN SS")])
print("[DOLAN SS] queda:", co.partner_id.l10n_ar_afip_responsibility_type_id.name)
env.cr.commit()
print("COMMIT OK")
