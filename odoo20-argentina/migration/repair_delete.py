import json
import os
import sys

BASE = "/tmp/migration/data"
load = lambda n: json.load(open(os.path.join(BASE, n), encoding="utf-8"))  # noqa: E731
invoices = load("invoices.json")
imap = {int(k): v for k, v in json.load(open("/tmp/invoice_map.json")).items()}
by_id = {r["rowid"]: r for r in invoices}

Move = env["account.move"]  # noqa: F821

def bad(rid, mid):
    src = by_id[rid]
    m = Move.browse(mid)
    return abs(abs(m.amount_total) - abs(float(src["total_ttc"] or 0))) > 0.02

limit = int(os.environ.get("REPAIR_LIMIT", "0"))
deleted = []
errors = []
for rid, mid in list(imap.items()):
    if not bad(rid, mid):
        continue
    src = by_id[rid]
    m = Move.browse(mid)
    if m.state == "posted" or m.payment_ids or m.amount_residual != m.amount_total:
        pass
    try:
        if m.line_ids:
            m.line_ids.remove_move_reconcile()
        for p in m.payment_ids:
            if p.state in ("posted", "cancelled"):
                p.button_draft()
            p.unlink()
        if m.state != "draft":
            m.button_draft()
        m.unlink()
        if str(rid) in imap:
            del imap[str(rid)]
        imap.pop(rid, None)
        deleted.append(src["ref"])
    except Exception as e:
        errors.append({"ref": src["ref"], "err": f"{type(e).__name__}: {e}"[:160]})
    if limit and len(deleted) >= limit:
        break

with open("/tmp/invoice_map.json", "w") as fh:
    json.dump(imap, fh)
print("borradas:", len(deleted), deleted[:8])
print("errores:", len(errors))
for e in errors[:5]:
    print("  ERR", e)
if errors:
    sys.exit(2)
env.cr.commit()
print("COMMIT OK")
