from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_send_invoice_whatsapp(self):
        """Abre el mensaje de WhatsApp precargado con los datos de la factura."""
        self.ensure_one()
        partner = self.partner_id
        body = "Hola %s, te compartimos la factura %s por %s." % (
            partner.name or "-", self.name or "-", self.amount_total)
        return {
            "type": "ir.actions.act_window",
            "name": "Enviar WhatsApp",
            "res_model": "dolan.whatsapp.message",
            "view_mode": "form",
            "views": [[False, "form"]],
            "target": "new",
            "context": {
                "default_partner_id": partner.id,
                "default_direction": "out",
                "default_body": body,
            },
        }
