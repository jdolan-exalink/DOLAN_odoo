import base64

raw = open("/tmp/logowebDOLANSS.png", "rb").read()
logo = base64.b64encode(raw)

def set_logo(rec):
    try:
        rec.logo = logo.decode("ascii")
    except TypeError:
        from odoo.tools.binary import BinaryValue
        rec.logo = BinaryValue(raw)
    try:
        rec.logo_web = logo.decode("ascii")
    except TypeError:
        from odoo.tools.binary import BinaryValue
        rec.logo_web = BinaryValue(raw)
HEADER = dict(street="Lavalle 4242", zip="3000", city="Santa Fe",
              phone="03425511820", email="jdolan@exalink.com.ar",
              website="www.dolan.com.ar")
states = env["res.country.state"].search([  # noqa: F821
    ("country_id", "=", env.ref("base.ar").id), ("name", "ilike", "Santa Fe")], limit=1)
for co in env["res.company"].browse([5, 6, 7]):  # noqa: F821
    set_logo(co)
    vals = dict(HEADER)
    if states:
        vals["state_id"] = states.id
    co.partner_id.write(vals)
    print(f"[{co.name}] logo {len(raw)}b, street={co.partner_id.street}, "
          f"city={co.partner_id.city}, zip={co.partner_id.zip}, state={co.partner_id.state_id.name}")
env.cr.commit()
print("COMMIT OK")
