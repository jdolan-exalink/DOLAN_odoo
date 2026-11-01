from odoo import fields, models


class DolanNotification(models.Model):
    """F6 — PRD04: unified attention centre items. Four kinds (informative,
    action required, warning, critical). The controller scopes every read and
    write to the owner user (no global rules needed)."""

    _name = "dolan.notification"
    _description = "DOLAN notification"
    _order = "create_date desc"

    name = fields.Char(required=True, string="Title")
    body = fields.Text(string="Details")
    kind = fields.Selection([
        ("info", "Informative"),
        ("action", "Action required"),
        ("warn", "Warning"),
        ("critical", "Critical"),
    ], required=True, default="info", string="Kind")
    state = fields.Selection([
        ("pending", "Pending"),
        ("read", "Read"),
        ("snoozed", "Snoozed"),
    ], required=True, default="pending", string="Status")
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    res_model = fields.Char(string="Related model")
    res_id = fields.Integer(string="Related record")
    snooze_until = fields.Datetime(string="Snoozed until")

    def action_read(self):
        self.write({"state": "read", "snooze_until": False})
        return True

    def action_snooze(self, minutes=30):
        self.write({"state": "snoozed",
                    "snooze_until": fields.Datetime.now() + fields.timedelta(minutes=minutes)})
        return True
