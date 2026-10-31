from odoo import api, fields, models

from odoo.addons.DOLAN_contabilidad.models.financial_report import (
    ACTIVO_CORRIENTE, ACTIVO_NO_CORRIENTE, COSTOS, GASTOS, INGRESOS,
    PASIVO_CORRIENTE, PASIVO_NO_CORRIENTE, PATRIMONIO,
)


class DolanAnnualReport(models.TransientModel):
    """Reporte anual propio (LGPL): resumen de resultados, balance resumido
    e indice de archivos de trabajo del ejercicio. Sin codigo Enterprise."""

    _name = "dolan.annual.report"
    _description = "Reporte anual del ejercicio"

    date_from = fields.Date(string="Desde", required=True,
                            default=lambda self: fields.Date.context_today(self).replace(month=1, day=1))
    date_to = fields.Date(string="Hasta", required=True,
                          default=lambda self: fields.Date.context_today(self).replace(month=12, day=31))

    def _sums(self, date_from=None, date_to=None):
        self.ensure_one()
        domain = [("company_id", "=", self.env.company.id), ("parent_state", "=", "posted")]
        if date_from:
            domain.append(("date", ">=", date_from))
        if date_to:
            domain.append(("date", "<=", date_to))
        totals = {}
        for line in self.env["account.move.line"].search(domain):
            totals[line.account_id.account_type] = totals.get(line.account_id.account_type, 0.0) + (line.balance or 0.0)
        return totals

    @api.model
    def _group(self, totals, types):
        return sum(totals.get(t, 0.0) for t in types)

    def action_generate(self):
        self.ensure_one()
        action = self.env.ref("DOLAN_contabilidad.action_annual_report_xlsx")
        return action.report_action(self, config=False)
