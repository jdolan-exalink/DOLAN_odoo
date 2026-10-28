import math
from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DolanAlquilerContrato(models.Model):
    _name = "dolan.alquiler.contrato"
    _description = "Contrato de alquiler por dia"
    _order = "fecha_inicio desc, id desc"

    name = fields.Char(required=True, default=lambda s: _("Nuevo contrato"))
    partner_id = fields.Many2one("res.partner", string="Cliente", required=True)
    product_id = fields.Many2one("product.product", string="Bien", required=True)
    fecha_inicio = fields.Date(required=True, default=fields.Date.context_today)
    fecha_fin = fields.Date(required=True)
    tarifa_dia = fields.Float(string="Tarifa por dia", required=True, default=1.0)
    currency_id = fields.Many2one(related="partner_id.currency_id")
    state = fields.Selection([
        ("borrador", "Borrador"),
        ("activo", "Activo"),
        ("finalizado", "Finalizado"),
        ("cancelado", "Cancelado"),
    ], default="borrador", required=True)
    dias = fields.Integer(compute="_compute_importes")
    total = fields.Float(compute="_compute_importes")
    move_id = fields.Many2one("account.move", string="Factura", readonly=True)

    @api.depends("fecha_inicio", "fecha_fin", "tarifa_dia")
    def _compute_importes(self):
        for c in self:
            if c.fecha_inicio and c.fecha_fin and c.fecha_fin >= c.fecha_inicio:
                dias = (c.fecha_fin - c.fecha_inicio).days + 1
            else:
                dias = 0
            c.dias = dias
            c.total = round(dias * (c.tarifa_dia or 0.0), 2)

    def action_iniciar(self):
        for c in self:
            if c.dias <= 0:
                raise UserError(_("Fechas invalidas: fin >= inicio."))
            c.state = "activo"

    def action_finalizar(self):
        self.write({"state": "finalizado"})

    def action_cancelar(self):
        self.write({"state": "cancelado"})

    def action_facturar(self):
        self.ensure_one()
        if self.move_id:
            raise UserError(_("Ya existe factura para este contrato."))
        if self.dias <= 0:
            raise UserError(_("No hay dias facturables."))
        move = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_id.id,
            "invoice_date": fields.Date.context_today(self),
            "ref": self.name,
            "invoice_line_ids": [(0, 0, {
                "name": _("Alquiler %s (%s a %s) — %s dias") % (
                    self.product_id.display_name, self.fecha_inicio, self.fecha_fin, self.dias),
                "quantity": self.dias,
                "price_unit": self.tarifa_dia,
                "product_id": self.product_id.id,
            })],
        })
        self.move_id = move
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "target": "current",
        }
