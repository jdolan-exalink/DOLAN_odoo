from odoo import api, fields, models

# Tipos de cuenta de Odoo 20 usados por los estados financieros.
ACTIVO_CORRIENTE = ["asset_receivable", "asset_cash", "asset_current", "asset_prepayments"]
ACTIVO_NO_CORRIENTE = ["asset_fixed", "asset_non_current"]
PASIVO_CORRIENTE = ["liability_payable", "liability_credit_card", "liability_current"]
PASIVO_NO_CORRIENTE = ["liability_non_current"]
PATRIMONIO = ["equity", "equity_unaffected"]
INGRESOS = ["income", "income_other"]
COSTOS = ["expense_direct_cost"]
GASTOS = ["expense", "expense_other", "expense_depreciation"]


class DolanFinancialReport(models.TransientModel):
    _name = "dolan.financial.report"
    _description = "Estados financieros DOLAN (Balance / Resultados / Flujo)"

    report_type = fields.Selection(
        selection=[
            ("balance", "Balance general"),
            ("results", "Estado de resultados"),
            ("cash", "Estado de flujo de efectivo (bancos y caja)"),
        ],
        string="Estado", required=True, default="balance",
    )
    date_from = fields.Date(
        string="Desde", required=True,
        default=lambda self: fields.Date.context_today(self).replace(month=1, day=1),
    )
    date_to = fields.Date(
        string="Hasta", required=True, default=fields.Date.context_today,
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wiz in self:
            if wiz.date_from and wiz.date_to and wiz.date_from > wiz.date_to:
                raise models.ValidationError(self.env._("La fecha desde no puede ser posterior a la fecha hasta."))

    # ------------------------------------------------------------------
    # Cálculos: sumas de account.move.line por tipo de cuenta. El saldo
    # (balance) se toma desde el inicio de los tiempos para activo/pasivo/
    # patrimonio; el resultado del ejercicio usa el acumulado también.
    # ------------------------------------------------------------------
    def _sum(self, account_types, date_from=None, date_to=None):
        self.ensure_one()
        domain = [
            ("company_id", "=", self.env.company.id),
            ("parent_state", "=", "posted"),
            ("account_id.account_type", "in", account_types),
        ]
        if date_from:
            domain.append(("date", ">=", date_from))
        if date_to:
            domain.append(("date", "<=", date_to))
        return sum(self.env["account.move.line"].search(domain).mapped("balance"))

    def _sums_by_type(self, date_from=None, date_to=None):
        """Devuelve {tipo_de_cuenta: saldo} en una sola pasada."""
        self.ensure_one()
        domain = [
            ("company_id", "=", self.env.company.id),
            ("parent_state", "=", "posted"),
        ]
        if date_from:
            domain.append(("date", ">=", date_from))
        if date_to:
            domain.append(("date", "<=", date_to))
        res = {}
        for line in self.env["account.move.line"].search(domain):
            tipo = line.account_id.account_type
            res[tipo] = res.get(tipo, 0.0) + (line.balance or 0.0)
        return res

    def _group(self, totals, types):
        return sum(totals.get(t, 0.0) for t in types)

    def action_generate(self):
        self.ensure_one()
        # config=False: sin el configurador de layout de cartuchos (no aplica a XLSX)
        action = self.env.ref("DOLAN_contabilidad.action_financial_report_xlsx")
        return action.report_action(self, config=False)
