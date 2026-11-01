"""F6 — PRD04: notification centre endpoints. Every query is scoped to the
current user inside the controller (no record rules required)."""
from odoo import http
from odoo.http import request


class DolanNotifications(http.Controller):

    def _own(self, notification_id):
        rec = request.env["dolan.notification"].browse(int(notification_id))
        return rec if rec.exists() and rec.user_id == request.env.user else None

    @http.route("/dolan/notifications", type="jsonrpc", auth="user")
    def notifications(self, **kw):
        env = request.env
        Model = env["dolan.notification"]
        items = Model.search([("user_id", "=", env.uid)], limit=25)
        counts = {"info": 0, "action": 0, "warn": 0, "critical": 0}
        out = []
        for n in items:
            if n.state != "pending":
                continue
            counts[n.kind] = counts.get(n.kind, 0) + 1
            out.append({
                "id": n.id, "name": n.name, "body": n.body or "", "kind": n.kind,
                "state": n.state, "res_model": n.res_model or "", "res_id": n.res_id or 0,
                "create_date": n.create_date.strftime("%d/%m %H:%M") if n.create_date else "",
            })
        return {"items": out, "counts": counts, "pending": len(out)}

    @http.route("/dolan/notifications/read", type="jsonrpc", auth="user")
    def mark_read(self, notification_id=0, **kw):
        rec = self._own(notification_id)
        if rec:
            rec.action_read()
        return {"ok": bool(rec)}

    @http.route("/dolan/notifications/snooze", type="jsonrpc", auth="user")
    def snooze(self, notification_id=0, minutes=30, **kw):
        rec = self._own(notification_id)
        if rec:
            rec.action_snooze(int(minutes or 30))
        return {"ok": bool(rec)}
