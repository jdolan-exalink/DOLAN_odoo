from odoo import api, fields, models


class DolanJournalAudit(models.TransientModel):
    _name = "dolan.journal.audit"
    _description = "Auditoría de diario DOLAN (asientos, saldos y secuencias)"

    date_from = fields.Date(
        string="Desde", required=True,
        default=lambda self: fields.Date.context_today(self).replace(month=1, day=1),
    )
    date_to = fields.Date(
        string="Hasta", required=True, default=fields.Date.context_today,
    )
    journal_id = fields.Many2one(
        "account.journal", string="Diario",
        domain="[('company_id', '=', company_id)]",
    )
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company,
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wiz in self:
            if wiz.date_from and wiz.date_to and wiz.date_from > wiz.date_to:
                raise models.ValidationError(self.env._("La fecha desde no puede ser posterior a la fecha hasta."))

    def _moves(self):
        """Asientos publicados del período (opcionalmente de un diario)."""
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("state", "=", "posted"),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]
        if self.journal_id:
            domain.append(("journal_id", "=", self.journal_id.id))
        return self.env["account.move"].search(domain, order="journal_id, name")

    def _move_amounts(self, move):
        """(debe, haber) del asiento desde sus apuntes."""
        debit = sum(move.line_ids.mapped("debit"))
        credit = sum(move.line_ids.mapped("credit"))
        return debit, credit

    def action_generate(self):
        self.ensure_one()
        # config=False: sin el configurador de cartuchos (no aplica a XLSX)
        action = self.env.ref("DOLAN_contabilidad.action_journal_audit_xlsx")
        return action.report_action(self, config=False)
