from datetime import date

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DolanFiscalPeriodo(models.Model):
    _name = "dolan.fiscal.periodo"
    _description = "Periodo fiscal de cierre"
    _order = "fecha_desde desc, id desc"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True)
    company_id = fields.Many2one("res.company", default=lambda s: s.env.company, required=True)
    fecha_desde = fields.Date(required=True)
    fecha_hasta = fields.Date(required=True)
    state = fields.Selection([
        ("abierto", "Abierto"),
        ("cerrado", "Cerrado"),
    ], default="abierto", required=True)
    item_ids = fields.One2many("dolan.fiscal.item", "periodo_id", string="Checklist")
    progreso = fields.Integer(compute="_compute_progreso")

    _sql_constraints = [
        ("rango_valido", "CHECK (fecha_hasta >= fecha_desde)", "El cierre no puede terminar antes de empezar."),
    ]

    @api.depends("item_ids.done")
    def _compute_progreso(self):
        for p in self:
            total = len(p.item_ids)
            p.progreso = round(100 * sum(1 for i in p.item_ids if i.done) / total) if total else 0

    @api.model
    def crear_checklist(self, periodo):
        """Items base del cierre AR (creados una vez por periodo)."""
        items = [
            ("iva_ventas", "IVA ventas: libro IVA digital del periodo"),
            ("iva_compras", "IVA compras: alicuotas y percepciones"),
            ("cae_pendientes", "Facturas con CAE pendiente de emision"),
            ("libro_diario", "Libro diario sin asientos en borrador"),
            ("retenciones", "Retenciones y percepciones registradas"),
            ("banco", "Conciliacion bancaria del periodo"),
        ]
        for ref, nombre in items:
            self.env["dolan.fiscal.item"].create({
                "periodo_id": periodo.id, "clave": ref, "name": nombre,
            })

    @api.model_create_multi
    def create(self, vals_list):
        periodos = super().create(vals_list)
        for p in periodos:
            self.crear_checklist(p)
        return periodos

    def datos_iva(self):
        """IVA del periodo desde account.move.line (debito = negativo)."""
        self.ensure_one()
        aml = self.env["account.move.line"].sudo().search([
            ("date", ">=", self.fecha_desde),
            ("date", "<=", self.fecha_hasta),
            ("tax_line_id", "!=", False),
            ("move_id.state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
        ])
        debito = -sum(aml.filtered(lambda l: l.balance < 0).mapped("balance"))
        credito = sum(aml.filtered(lambda l: l.balance > 0).mapped("balance"))
        return {"debito": round(debito, 2), "credito": round(credito, 2),
                "saldo": round(debito - credito, 2)}

    def cae_pendientes(self):
        """Facturas borrador/posted sin CAE (contabilizadas pendientes de CAE)."""
        self.ensure_one()
        return self.env["account.move"].sudo().search_count([
            ("date", ">=", self.fecha_desde),
            ("date", "<=", self.fecha_hasta),
            ("state", "=", "posted"),
            ("l10n_ar_fiscal_auth_code", "=", False),
        ])

    def action_cerrar(self):
        for p in self:
            faltan = p.item_ids.filtered(lambda i: not i.done)
            if faltan:
                raise UserError(_("Items sin marcar: %s") % ", ".join(faltan.mapped("name")[:3]))
            p.state = "cerrado"

    def action_reabrir(self):
        self.write({"state": "abierto"})


class DolanFiscalItem(models.Model):
    _name = "dolan.fiscal.item"
    _description = "Item del checklist fiscal"
    _order = "id"

    periodo_id = fields.Many2one("dolan.fiscal.periodo", required=True, ondelete="cascade")
    clave = fields.Char()
    name = fields.Char(string="Item", required=True)
    done = fields.Boolean(string="Hecho")
    notas = fields.Text()
