from odoo import api, fields, models
from odoo.exceptions import UserError

# Jurisdicciones habilitadas (S11): nombre, codigo de provincia AR y partner
# por defecto para el pago. La alicuota es PARAMETRO: verificar la vigente en
# cada jurisdiccion antes de usarla en produccion.
PROVINCIAS = [
    ("SF", "Santa Fe", "IIBB Santa Fe"),
    ("ER", "Entre Rios", "IIBB Entre Rios"),
    ("BA", "Buenos Aires", "IIBB Buenos Aires"),
    ("CBA", "Cordoba", "IIBB Cordoba"),
]


class DolanIibbWizard(models.TransientModel):
    _name = "dolan.iibb.wizard"
    _description = "Registro de retencion/percepcion de IIBB"

    factura = fields.Many2one(
        "account.move", string="Factura de compra", required=True,
        domain="[('move_type', '=', 'in_invoice'), ('state', '=', 'posted')]")
    provincia = fields.Selection(
        selection=[(c, n) for c, n, _p in PROVINCIAS],
        string="Provincia", required=True, default="SF")
    tipo = fields.Selection(
        selection=[("retencion", "Retencion"), ("percepcion", "Percepcion")],
        string="Tipo", required=True, default="retencion")
    base = fields.Float(string="Base imponible", digits=(16, 2))
    alicuota = fields.Float(string="Alicuota (%)", default=3.0, digits=(16, 4))
    monto = fields.Float(string="Monto", compute="_compute_monto", digits=(16, 2))
    journal_id = fields.Many2one(
        "account.journal", string="Diario (cuenta del haber)", required=True,
        domain="[('type', 'in', ('bank', 'cash'))]")
    cuenta_debe = fields.Many2one(
        "account.account", string="Cuenta del debe", required=True,
        domain="[('account_type', '!=', 'off_balance')]",
        help="Cuenta de tributos/percepciones (ej.: IIBB a pagar o anticipos).")
    partner_id = fields.Many2one(
        "res.partner", string="Proveedor / jurisdiccion",
        help="Se crea uno por provincia si no existe.")
    move_id = fields.Many2one("account.move", string="Asiento creado", readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if res.get("factura") or "factura" not in fields_list:
            return res
        active_id = self.env.context.get("active_id")
        move = self.env["account.move"].browse(active_id) if active_id else self.env["account.move"]
        if move.exists() and move.move_type == "in_invoice" and move.state == "posted":
            res["factura"] = move.id
            res["base"] = move.amount_untaxed
        return res

    @api.onchange("factura")
    def _onchange_factura(self):
        if self.factura and not self.base:
            self.base = self.factura.amount_untaxed

    @api.depends("base", "alicuota")
    def _compute_monto(self):
        for w in self:
            w.monto = round((w.base or 0.0) * (w.alicuota or 0.0) / 100.0, 2)

    def _jurisdiccion_partner(self):
        """Partner de la jurisdiccion (creado si no existe)."""
        self.ensure_one()
        nombre = dict((c, n) for c, n, _p in PROVINCIAS)[self.provincia]
        Partner = self.env["res.partner"]
        p = Partner.search([("name", "=", nombre)], limit=1)
        if not p:
            p = Partner.create({"name": nombre, "supplier_rank": 1})
        return p

    def action_create_move(self):
        """Registra la retencion/percepcion como asiento (debe tributo / haber banco)."""
        self.ensure_one()
        if not self.monto or self.monto <= 0:
            raise UserError("El monto debe ser mayor a cero.")
        if not self.factura:
            raise UserError("Elija la factura de compra asociada.")
        if not self.journal_id.default_account_id:
            raise UserError(
                "El diario %s no tiene cuenta contable: asigela en Ajustes > Diarios."
                % self.journal_id.name)
        partner = self.partner_id or self._jurisdiccion_partner()
        tipo = "Retencion" if self.tipo == "retencion" else "Percepcion"
        provincia = dict((c, n) for c, n, _p in PROVINCIAS)[self.provincia]
        ref = ("%s IIBB %s - %s" % (tipo, provincia, self.factura.name or ""))[:200]
        move = self.env["account.move"].create({
            "move_type": "entry",
            "date": fields.Date.context_today(self),
            "ref": ref,
            "narration": "Factura de compra asociada: %s (base %s, alicuota %s%%)"
                         % (self.factura.name or "-", self.base, self.alicuota),
            "line_ids": [
                (0, 0, {"name": ref, "account_id": self.cuenta_debe.id,
                        "partner_id": partner.id, "debit": self.monto, "credit": 0.0}),
                (0, 0, {"name": ref, "account_id": self.journal_id.default_account_id.id,
                        "partner_id": partner.id, "credit": self.monto, "debit": 0.0}),
            ],
        })
        move.action_post()
        self.write({"partner_id": partner.id, "move_id": move.id})
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": move.id,
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "current",
        }
