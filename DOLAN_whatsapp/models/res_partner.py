from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_send_whatsapp(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Enviar WhatsApp",
            "res_model": "dolan.whatsapp.message",
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "new",
            "context": {"default_partner_id": self.id, "default_direction": "out"},
        }
