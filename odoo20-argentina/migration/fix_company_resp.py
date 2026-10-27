import sys

CTX_RESP = {"1": "l10n_ar.res_IVARI", "2": "l10n_ar.res_MON_Ind", "3": "l10n_ar.res_MON_Ind"}
NAME2ENT = {"DOLAN SS": "1", "JUAN MARTIN DOLAN": "2", "CINTIA VERONICA GOROSITO": "3"}

for co in env["res.company"].search([("id", "in", [5, 6, 7])]):  # noqa: F821
    ent = NAME2ENT[co.name]
    resp = env.ref(CTX_RESP[ent])
    co.partner_id.l10n_ar_afip_responsibility_type_id = resp
    print(f"[{co.name}] responsabilidad -> {resp.name} (code {resp.code})")

env.cr.commit()
print("COMMIT OK")
