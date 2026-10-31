from odoo import fields, models


class L10nLatamCheck(models.Model):
    """Cheques rechazados (C11 propio, estilo EE; sin tocar OCA ni OPL-1)."""

    _inherit = "l10n_latam.check"

    dolan_rejected = fields.Boolean("Rechazado", copy=False, default=False)
    dolan_rejected_date = fields.Date("Fecha de rechazo", copy=False)
    dolan_rejected_reason = fields.Char("Motivo / observacion")

    def action_mark_rejected(self):
        today = fields.Date.context_today(self)
        for check in self:
            if not check.dolan_rejected:
                check.write({"dolan_rejected": True, "dolan_rejected_date": today})
        return True

    def action_clear_rejected(self):
        self.write({"dolan_rejected": False, "dolan_rejected_date": False,
                    "dolan_rejected_reason": False})
        return True
