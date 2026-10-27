U = env["res.users"].sudo()  # noqa: F821
Co = env["res.company"].sudo()

moved = []
for u in U.search([("company_id", "=", 1)]):
    u.write({"company_id": 5, "company_ids": [(6, 0, [5, 6, 7])]})
    moved.append(f"user {u.id} {u.login} -> company 5")
for u in U.search([]):
    have = u.company_ids.ids
    keep = [c for c in have if c != 1] or [5]
    if have != keep:
        u.write({"company_ids": [(6, 0, keep)]})
        moved.append(f"user {u.id} {u.login} company_ids {have} -> {keep}")
for line in moved:
    print("MOVE:", line)

c1 = Co.browse(1).with_context(active_test=False)
print("antes: company1", repr(c1.name), "active", c1.active, "| partner", repr(c1.partner_id.name), c1.partner_id.active)
c1.write({"active": False})
if c1.partner_id.active:
    c1.partner_id.write({"active": False})
try:
    env["ir.default"].sudo().search([("company_id", "=", 1)]).unlink()
except Exception as error:
    print("ir.default company1 skip:", type(error).__name__)
env.cr.commit()
print("COMMIT OK")

activas = Co.search([]).mapped("name")
print("companies activas:", activas)
print("users:", [(u.id, u.login, u.company_id.name) for u in U.search([]) ])
