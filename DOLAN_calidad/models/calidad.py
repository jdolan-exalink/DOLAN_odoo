from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DolanCalidadPuntoControl(models.Model):
    _name = "dolan.calidad.punto_control"
    _description = "Punto de control de calidad"

    name = fields.Char(required=True)
    ambito = fields.Selection([
        ("producto", "Producto"),
        ("operacion", "Operacion"),
    ], default="producto", required=True)
    product_id = fields.Many2one("product.product", string="Producto", ondelete="set null")
    instrucciones = fields.Text()
    activo = fields.Boolean(default=True)


class DolanCalidadControl(models.Model):
    _name = "dolan.calidad.control"
    _description = "Control de calidad ejecutado"
    _order = "fecha desc, id desc"

    name = fields.Char(required=True, default=lambda s: _("Control"))
    punto_id = fields.Many2one("dolan.calidad.punto_control", string="Punto de control", required=True)
    referencia = fields.Char(string="Referencia (OP/remito)", help="Orden de produccion, remito o lote relacionado")
    fecha = fields.Date(required=True, default=fields.Date.context_today)
    responsable_id = fields.Many2one("res.users", default=lambda s: s.env.uid)
    resultado = fields.Selection([
        ("pendiente", "Pendiente"),
        ("ok", "OK"),
        ("ko", "KO"),
    ], default="pendiente", required=True)
    observaciones = fields.Text()
    nc_ids = fields.One2many("dolan.calidad.no_conformidad", "control_id", string="No conformidades")

    def action_marcar_ok(self):
        for c in self:
            if c.resultado == "ko" and c.nc_ids:
                raise UserError(_("El control KO tiene no conformidades: gestionalas desde ahi."))
            c.resultado = "ok"

    def action_marcar_ko(self):
        for c in self:
            if c.resultado == "ko":
                continue
            c.resultado = "ko"
            if not c.nc_ids:
                self.env["dolan.calidad.no_conformidad"].create({
                    "control_id": c.id,
                    "descripcion": _("No conformidad detectada en %s") % c.punto_id.name,
                })


class DolanCalidadNoConformidad(models.Model):
    _name = "dolan.calidad.no_conformidad"
    _description = "No conformidad de calidad"
    _order = "estado, id desc"

    control_id = fields.Many2one("dolan.calidad.control", string="Control", required=True, ondelete="cascade")
    partner_id = fields.Many2one(related="control_id.punto_id.product_id.company_id", store=False)
    product_id = fields.Many2one(related="control_id.punto_id.product_id", string="Producto")
    descripcion = fields.Text(required=True)
    estado = fields.Selection([
        ("abierta", "Abierta"),
        ("cerrada", "Cerrada"),
    ], default="abierta", required=True)
    solucion = fields.Text()

    def action_cerrar(self):
        for nc in self:
            if not nc.solucion:
                raise UserError(_("Defini la solucion antes de cerrar."))
            nc.estado = "cerrada"
