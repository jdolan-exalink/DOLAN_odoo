from odoo import models

# Plantilla por defecto del comprobante. Se puede sobreescribir con el
# parametro dolan.waha.invoice_template (placeholders: {socio} {tipo}
# {comprobante} {empresa} {fecha} {importe} {moneda} {cae} {cae_vence}
# {vencimiento} {enlace}).
PLANTILLA_COMPROBANTE = (
    "Hola {socio}, te compartimos {tipo} {comprobante} de {empresa}.\n"
    "Fecha: {fecha}\n"
    "Importe: {importe} {moneda}\n"
    "CAE: {cae}{cae_vence}\n"
    "Vencimiento: {vencimiento}\n"
    "Ver comprobante: {enlace}"
)

TIPOS = {
    "out_invoice": "Factura",
    "out_refund": "Nota de crédito",
    "in_invoice": "Factura de compra",
    "in_refund": "Nota de crédito de compra",
}


def _ar(n):
    """Formato argentino: 1.234,56"""
    s = f"{n:,.2f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


class AccountMove(models.Model):
    _inherit = "account.move"

    def _dolan_whatsapp_body(self):
        """Cuerpo del mensaje con los datos del comprobante (CAE, total, link)."""
        self.ensure_one()
        partner = self.partner_id
        params = self.env["ir.config_parameter"].sudo()
        plantilla = params.get_str("dolan.waha.invoice_template", "") or PLANTILLA_COMPROBANTE

        cae = self.l10n_ar_fiscal_auth_code if "l10n_ar_fiscal_auth_code" in self._fields else False
        cae_due = (self.l10n_ar_fiscal_auth_code_due
                   if "l10n_ar_fiscal_auth_code_due" in self._fields else False)
        try:
            enlace = self.get_portal_url() or ""
            if enlace.startswith("/"):
                enlace = (self.get_base_url() or "").rstrip("/") + enlace
        except Exception:  # noqa: BLE001
            enlace = ""
        campos = {
            "socio": partner.name or "-",
            "tipo": TIPOS.get(self.move_type, "Comprobante"),
            "comprobante": self.name or "-",
            "empresa": self.company_id.name or "-",
            "fecha": self.invoice_date.strftime("%d/%m/%Y") if self.invoice_date else "-",
            "importe": _ar(self.amount_total or 0.0),
            "moneda": (self.currency_id or self.company_id.currency_id).name or "",
            "cae": cae or "sin CAE",
            "cae_vence": f" (vence {cae_due.strftime('%d/%m/%Y')})" if cae_due else "",
            "vencimiento": (self.invoice_date_due.strftime("%d/%m/%Y")
                            if self.invoice_date_due else "-"),
            "enlace": enlace or "-",
        }
        try:
            cuerpo = plantilla.format(**campos)
        except (KeyError, IndexError, ValueError):
            cuerpo = PLANTILLA_COMPROBANTE.format(**campos)
        # se limpian las lineas cuyo valor quedo vacio (ej. CAE sin vencimiento)
        lineas = [l for l in cuerpo.split("\n") if not l.rstrip().endswith(":")]
        return "\n".join(lineas).strip()

    def action_send_invoice_whatsapp(self):
        """Abre el mensaje de WhatsApp precargado con los datos de la factura."""
        self.ensure_one()
        partner = self.partner_id
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
                "default_body": self._dolan_whatsapp_body(),
            },
        }
