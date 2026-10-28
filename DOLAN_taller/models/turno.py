from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DolanTallerTurno(models.Model):
    _name = "dolan.taller.turno"
    _description = "Turno de trabajo en centro de trabajo"
    _order = "inicio desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(default=lambda s: _("Turno"), required=True)
    workcenter_id = fields.Many2one("mrp.workcenter", string="Centro de trabajo", required=True)
    workorder_id = fields.Many2one("mrp.workorder", string="Orden de trabajo")
    production_id = fields.Many2one(related="workorder_id.production_id", store=True, readonly=False)
    operador_id = fields.Many2one("res.users", string="Operador", default=lambda s: s.env.uid)
    state = fields.Selection([
        ("corriendo", "En curso"),
        ("pausado", "Pausado"),
        ("terminado", "Terminado"),
    ], default="corriendo", required=True)
    inicio = fields.Datetime(required=True, default=fields.Datetime.now)
    fin = fields.Datetime()
    minutos = fields.Float(compute="_compute_minutos", string="Minutos")
    consumo_ids = fields.One2many("dolan.taller.consumo", "turno_id", string="Materiales")
    qc_ids = fields.One2many("dolan.calidad.control", "taller_turno_id", string="Controles de calidad")

    @api.depends("inicio", "fin", "state")
    def _compute_minutos(self):
        ahora = fields.Datetime.now()
        for t in self:
            if not t.inicio:
                t.minutos = 0.0
                continue
            ref = t.fin or (ahora if t.state == "corriendo" else None)
            if not ref:
                t.minutos = 0.0
            else:
                delta = fields.Datetime.from_string(ref) - fields.Datetime.from_string(t.inicio)
                t.minutos = round(delta.total_seconds() / 60.0, 1)

    def action_pausar(self):
        for t in self:
            if t.state != "corriendo":
                raise UserError(_("El turno no esta en curso."))
            t.fin = fields.Datetime.now()
            t.state = "pausado"

    def action_reanudar(self):
        for t in self:
            if t.state != "pausado":
                raise UserError(_("El turno no esta pausado."))
            t.inicio = fields.Datetime.now()
            t.fin = False
            t.state = "corriendo"

    def action_terminar(self):
        for t in self:
            if t.state == "terminado":
                continue
            if t.state == "corriendo":
                t.fin = fields.Datetime.now()
            t.state = "terminado"

    def qc_crear(self, punto_id):
        """Punto de control DOLAN_calidad atado a este turno."""
        self.ensure_one()
        return self.env["dolan.calidad.control"].create({
            "name": _("QC %s") % self.name,
            "punto_id": punto_id,
            "referencia": self.workorder_id.display_name if self.workorder_id else "",
            "taller_turno_id": self.id,
        })


class DolanCalidadControlExt(models.Model):
    _inherit = "dolan.calidad.control"

    # Enlace opcional al turno (solo existe con DOLAN_taller instalado)
    taller_turno_id = fields.Many2one("dolan.taller.turno", string="Turno de taller", ondelete="set null")


class DolanTallerConsumo(models.Model):
    _name = "dolan.taller.consumo"
    _description = "Consumo de material en turno"

    turno_id = fields.Many2one("dolan.taller.turno", required=True, ondelete="cascade")
    product_id = fields.Many2one("product.product", string="Material", required=True)
    cantidad = fields.Float(required=True, default=1.0)
    uom_id = fields.Many2one(related="product_id.uom_id")
