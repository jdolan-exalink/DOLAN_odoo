from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    dolan_last_reconcile = fields.Date(
        string="Último recobro",
        compute="_compute_dolan_last_reconcile",
        help="Última fecha de pago conciliado o reconciliación completa "
             "(columna estilo Enterprise, calculada sin modificar el core).",
    )

    def _compute_dolan_last_reconcile(self):
        for move in self:
            fecha = False
            for payment in move.payment_ids:
                if payment.date and (not fecha or payment.date > fecha):
                    fecha = payment.date
            if move.line_ids:
                # Odoo20: account.full.reconcile ya no expone debit/credit_move_id;
                # usamos las conciliaciones parciales (siempre con esos campos)
                partials = self.env["account.partial.reconcile"].search([
                    "|",
                    ("debit_move_id", "in", move.line_ids.ids),
                    ("credit_move_id", "in", move.line_ids.ids),
                ], limit=50)
                for part in partials:
                    d = part.create_date.date()
                    if d and (not fecha or d > fecha):
                        fecha = d
            move.dolan_last_reconcile = fecha
