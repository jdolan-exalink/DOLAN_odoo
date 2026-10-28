from datetime import date, timedelta

from odoo import api, fields, models, _


class DolanSuscripcionPlan(models.Model):
    _name = "dolan.suscripcion.plan"
    _description = "Plan de suscripcion"

    name = fields.Char(required=True)
    precio = fields.Float(string="Precio por periodo", required=True, default=1.0)
    ciclo_dias = fields.Integer(string="Dias por periodo", default=30, required=True)
    activo = fields.Boolean(default=True)
    product_id = fields.Many2one("product.product", string="Producto de facturacion")


class DolanSuscripcionSuscripcion(models.Model):
    _name = "dolan.suscripcion.suscripcion"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Suscripcion de cliente"
    _order = "fecha_inicio desc, id desc"

    name = fields.Char(required=True, default=lambda s: _("Nueva suscripcion"))
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True)
    plan_id = fields.Many2one("dolan.suscripcion.plan", string="Plan", required=True)
    fecha_inicio = fields.Date(required=True, default=fields.Date.context_today)
    fecha_ultima = fields.Date(string="Inicio del periodo vigente", required=True,
                               default=fields.Date.context_today,
                               help="Dia (>= inicio) desde el que se emite el ultimo periodo facturado; avanza el ciclo al facturar.")
    user_id = fields.Many2one("res.users", string="Vendedor",
                              default=lambda s: s.env.uid)
    fase = fields.Selection([
        ("cotizacion", "Cotizacion"),
        ("renovado", "Renovado"),
        ("venta_adicional", "Venta adicional"),
    ], default="renovado", required=True)
    state = fields.Selection([
        ("activa", "Activa"),
        ("pausada", "Pausada"),
        ("cancelada", "Cancelada"),
    ], default="activa", required=True)
    proxima = fields.Date(compute="_compute_proxima", store=True)

    @api.depends("fecha_ultima", "plan_id.ciclo_dias", "fecha_inicio")
    def _compute_proxima(self):
        for s in self:
            ciclo = s.plan_id.ciclo_dias or 30
            base = s.fecha_ultima or s.fecha_inicio
            s.proxima = base + timedelta(days=ciclo) if base else False

    @api.model
    def facturar_programadas(self, hoy=None):
        """Cron: genera una factura borrador por cada suscripcion activa vencida.
        Devuelve cantidad de facturas creadas."""
        hoy = hoy or date.today()
        creadas = 0
        subs = self.search([("state", "=", "activa")], limit=500)
        for sub in subs:
            if not sub.plan_id or sub.proxima > hoy:
                continue
            guard = 0
            while sub.proxima <= hoy and guard < 365:
                periodo_ini = sub.fecha_ultima or sub.fecha_inicio
                periodo_fin = sub.proxima - timedelta(days=1)
                self.env["account.move"].create({
                    "move_type": "out_invoice",
                    "partner_id": sub.partner_id.id,
                    "invoice_date": hoy,
                    "ref": f"{sub.name} {periodo_ini} a {periodo_fin}",
                    "invoice_line_ids": [(0, 0, {
                        "name": _("Suscripcion %s — periodo %s a %s") % (sub.plan_id.name, periodo_ini, periodo_fin),
                        "quantity": 1,
                        "price_unit": sub.plan_id.precio,
                        "product_id": sub.plan_id.product_id.id if sub.plan_id.product_id else False,
                    })],
                })
                creadas += 1
                sub.fecha_ultima = sub.proxima
                guard += 1
        return creadas
