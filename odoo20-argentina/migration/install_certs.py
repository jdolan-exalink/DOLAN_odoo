import os

MAP = {
    5: "dolanss",   # DOLAN SS 30-71903035-8
    6: "juan",      # JUAN MARTIN DOLAN 20-26694600-8
    7: "gorosito",  # CINTIA VERONICA GOROSITO 27-34563638-8
}
B = "/tmp/certs"

def read(name):
    with open(os.path.join(B, name), encoding="utf-8") as fh:
        return fh.read()

Alias = env["l10n_ar.fiscal.certificate.alias"].sudo()  # noqa: F821
Cert = env["l10n_ar.fiscal.certificate"].sudo()
Journal = env["account.journal"].sudo()

for co_id, base in MAP.items():
    co = env["res.company"].browse(co_id)
    key, crt = read(base + ".key"), read(base + ".crt")
    alias = Alias.search([("company_id", "=", co_id), ("type", "=", "production")], limit=1)
    if not alias:
        alias = Alias.create({
            "company_id": co_id,
            "common_name": ("AFIP WS wsfe - %s" % co.name)[:50],
            "company_cuit": co.vat,
            "country_id": co.country_id.id,
            "state_id": co.state_id.id or False,
            "city": co.city or False,
            "key": key,
        })
    if alias.state != "confirmed":
        alias.action_confirm()
    cert = Cert.search([("alias_id", "=", alias.id)], limit=1)
    if not cert:
        cert = Cert.create({"alias_id": alias.id, "crt": crt})
    if cert.state != "confirmed":
        cert.action_confirm()
    print(f"[{co.name}] alias={alias.state} cert={cert.state} cuit={alias.company_cuit}")

    # guard de l10n_ar: no deja cambiar pos_system con facturas validadas;
    # los numeros ya estan fijos (migrados), seteamos lo que el compute haria
    wsfe = env["l10n_ar.fiscal.ws"].sudo().search([("code", "=", "wsfe")], limit=1)
    env.cr.execute(
        "UPDATE account_journal SET l10n_ar_afip_pos_system='RAW_MAW', l10n_ar_fiscal_ws_id=%s "
        "WHERE company_id=%s AND type='sale' AND COALESCE(l10n_ar_fiscal_ws_id,0)<>%s",
        (wsfe.id, co_id, wsfe.id))
    sj = Journal.search([("company_id", "=", co_id), ("type", "=", "sale")], limit=1)
    sj.invalidate_recordset()
    print(f"   journal {sj.name}: pos_system={sj.l10n_ar_afip_pos_system} "
          f"ws={sj.l10n_ar_fiscal_ws_id.code} pv={sj.l10n_ar_afip_pos_number}")

env.cr.commit()
print("CONFIG COMMIT OK")

# Prueba WSAA: ticket de acceso de PRODUCCION explicito (el parametro global
# sigue en homologacion -> emision futura queda en fallback local hasta go-live)
for co_id in MAP:
    co = env["res.company"].browse(co_id)  # noqa: F821
    try:
        conn = co._create_fiscal_ws_connection("wsfe", "production")
        print(f"WSAA OK [{co.name}] gen={conn.generation_time} exp={conn.expiration_time} type={conn.type}")
        env.cr.commit()
    except Exception as error:
        print(f"WSAA FAIL [{co.name}]: {type(error).__name__}: {str(error)[:300]}")
