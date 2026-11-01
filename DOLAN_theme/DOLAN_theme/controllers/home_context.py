"""F3 — PRD04: role-aware home context (role, KPIs, alerts, tasks and
quick actions). Every query is model-guarded and access-guarded."""
from odoo import fields, http
from odoo.http import request
from odoo.exceptions import AccessError

# priority order: first match wins
ROLE_GROUPS = [
    ("gerencia", "Gerencia", ["base.group_system"]),
    ("administracion", "Administracion", ["account.group_account_manager", "account.group_account_user"]),
    ("ventas", "Ventas", ["sale.group_sale_manager", "sale.group_sale_salesman"]),
    ("compras", "Compras", ["purchase.group_purchase_manager", "purchase.group_purchase_user"]),
    ("deposito", "Deposito", ["stock.group_stock_manager", "stock.group_stock_user"]),
    ("produccion", "Produccion", ["mrp.group_mrp_user"]),
    ("mantenimiento", "Mantenimiento", ["maintenance.group_maintenance_user"]),
]
# ISP: no ISP vertical in this stack yet; documented as pending in the log.

QUICK_ACTIONS = {
    "gerencia": [("Contabilidad", "account.menu_finance"), ("Operaciones", "dolan_dash.menu_operaciones_root"), ("Contactos", "contacts.menu_contacts")],
    "administracion": [("Contabilidad", "account.menu_finance"), ("Cobranzas", "sale.sale_menu_root"), ("Contactos", "contacts.menu_contacts")],
    "ventas": [("Pipeline", "crm.crm_menu_root"), ("Ventas", "sale.sale_menu_root"), ("Contactos", "contacts.menu_contacts")],
    "compras": [("Compras", "purchase.menu_purchase_root"), ("Stock", "stock.menu_stock_root")],
    "deposito": [("Stock", "stock.menu_stock_root"), ("Compras", "purchase.menu_purchase_root")],
    "produccion": [("Produccion", "mrp.mrp_menu_root"), ("Stock", "stock.menu_stock_root")],
    "mantenimiento": [("Mantenimiento", "maintenance.menu_maintenance_root"), ("Operaciones", "dolan_dash.menu_operaciones_root")],
    "general": [("Contabilidad", "account.menu_finance"), ("Contactos", "contacts.menu_contacts")],
}


class DolanHomeContext(http.Controller):

    def _role(self, env):
        for key, label, groups in ROLE_GROUPS:
            for xmlid in groups:
                try:
                    if env.user.has_group(xmlid):
                        return key, label
                except Exception:
                    continue
        return "general", "Mi espacio"

    def _count(self, env, model, domain):
        if model not in env.registry:
            return None
        try:
            return env[model].search_count(domain)
        except AccessError:
            return None
        except Exception:
            return None

    @http.route("/dolan/home_context", type="jsonrpc", auth="user")
    def home_context(self, **kw):
        env = request.env
        today = fields.Date.today()
        role, label = self._role(env)
        kpis, alerts, tasks = [], [], []

        def add_kpi(text, value):
            if value is not None:
                kpis.append({"label": text, "value": value})

        open_inv = [("move_type", "in", ("out_invoice", "out_refund")),
                    ("state", "=", "posted"),
                    ("payment_state", "in", ("not_paid", "partial"))]
        if role in ("gerencia", "administracion", "general"):
            add_kpi("Comprobantes impagas", self._count(env, "account.move", open_inv))
            add_kpi("Vencidas", self._count(env, "account.move", open_inv + [("invoice_date_due", "<", today)]))
            add_kpi("Presupuestos abiertos", self._count(env, "sale.order", [("state", "in", ("draft", "sent"))]))
        if role == "ventas":
            add_kpi("Oportunidades abiertas", self._count(env, "crm.lead", [("active", "=", True), ("stage_id.is_won", "=", False)]))
            add_kpi("Presupuestos abiertos", self._count(env, "sale.order", [("state", "in", ("draft", "sent"))]))
            add_kpi("Pedidos a preparar", self._count(env, "sale.order", [("state", "=", "sale")]))
        if role == "compras":
            add_kpi("Ordenes borrador", self._count(env, "purchase.order", [("state", "=", "draft")]))
            add_kpi("Por recibir", self._count(env, "purchase.order", [("state", "=", "purchase")]))
        if role == "deposito":
            add_kpi("Remitos en curso", self._count(env, "stock.picking", [("state", "not in", ("done", "cancel"))]))
            add_kpi("Entradas pendientes", self._count(env, "stock.picking", [("state", "not in", ("done", "cancel")), ("picking_type_id.code", "=", "incoming")]))
        if role == "produccion":
            add_kpi("Ordenes en curso", self._count(env, "mrp.production", [("state", "in", ("confirmed", "progress", "to_close"))]))
        if role == "mantenimiento":
            add_kpi("Solicitudes de mantenimiento", self._count(env, "maintenance.request", []))
            add_kpi("Equipos", self._count(env, "maintenance.equipment", []))

        overdue = self._count(env, "account.move", open_inv + [("invoice_date_due", "<", today)])
        if overdue:
            alerts.append({"label": "%d facturas vencidas" % overdue, "tone": "critico"})
        late_act = self._count(env, "mail.activity", [("user_id", "=", env.uid), ("date_deadline", "<", today)])
        if late_act:
            alerts.append({"label": "%d actividades atrasadas" % late_act, "tone": "accion"})
        rejected = None
        if "account.payment" in env.registry:
            rejected = None
        my_acts = []
        if "mail.activity" in env.registry:
            try:
                acts = env["mail.activity"].search(
                    [("user_id", "=", env.uid)], order="date_deadline asc", limit=6)
                my_acts = [{"label": (a.res_name or a.activity_type_id.display_name or "Actividad")[:60],
                            "model": a.res_model, "id": a.res_id} for a in acts]
            except AccessError:
                my_acts = []
        return {
            "role": role,
            "role_label": label,
            "kpis": kpis,
            "alerts": alerts,
            "tasks": my_acts,
            "quick_actions": [{"label": l, "xmlid": x} for l, x in QUICK_ACTIONS.get(role, QUICK_ACTIONS["general"])],
        }
