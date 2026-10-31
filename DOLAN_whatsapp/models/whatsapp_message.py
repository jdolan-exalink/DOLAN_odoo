import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

PARAM_URL = "dolan.waha.url"
PARAM_KEY = "dolan.waha.api_key"
PARAM_SESSION = "dolan.waha.session"
PARAM_TOKEN = "dolan.waha.webhook_token"


class DolanWhatsappMessage(models.Model):
    _name = "dolan.whatsapp.message"
    _description = "Mensaje de WhatsApp (WAHA)"
    _order = "create_date desc"

    partner_id = fields.Many2one("res.partner", string="Contacto", index=True)
    direction = fields.Selection(
        [("out", "Enviado"), ("in", "Recibido")], string="Direccion",
        required=True, default="out")
    body = fields.Text(string="Mensaje", required=True)
    chat_id = fields.Char(string="Chat ID", index=True)
    status = fields.Selection(
        [("pending", "Pendiente"), ("sent", "Enviado"), ("received", "Recibido"),
         ("error", "Error")],
        string="Estado", default="pending", required=True)
    error = fields.Char(string="Error")
    external_id = fields.Char(string="ID WAHA", index=True)

    # ------------------------------------------------------------------
    # Configuracion (ir.config_parameter)
    # ------------------------------------------------------------------
    @api.model
    def _waha_config(self):
        params = self.env["ir.config_parameter"].sudo()
        return {
            "url": (params.get_str(PARAM_URL, "") or "http://waha:3000").rstrip("/"),
            "api_key": params.get_str(PARAM_KEY, ""),
            "session": params.get_str(PARAM_SESSION, "") or "default",
            "token": params.get_str(PARAM_TOKEN, ""),
        }

    @api.model
    def _chat_id(self, phone):
        phone = str(phone or "")
        digits = "".join(c for c in phone if c.isdigit())
        if not digits:
            return False
        return phone if "@" in phone else digits + "@c.us"

    # ------------------------------------------------------------------
    # Acciones del formulario
    # ------------------------------------------------------------------
    def action_send(self):
        for rec in self:
            self.send_text(rec.partner_id, rec.body)
        return True

    # ------------------------------------------------------------------
    # Envio por WAHA
    # ------------------------------------------------------------------
    @api.model
    def send_text(self, partner, body):
        partner.ensure_one()
        body = (body or "").strip()
        if not body:
            raise UserError(_("El mensaje no puede estar vacio."))
        cfg = self._waha_config()
        chat_id = self._chat_id(partner.phone)
        if not chat_id:
            raise UserError(_("El contacto no tiene telefono/movil para WhatsApp."))

        rec = self.create({
            "partner_id": partner.id,
            "direction": "out",
            "body": body,
            "chat_id": chat_id,
            "status": "pending",
        })
        headers = {"Content-Type": "application/json"}
        if cfg["api_key"]:
            headers["X-Api-Key"] = cfg["api_key"]
        try:
            resp = requests.post(
                cfg["url"] + "/api/sendText",
                json={"session": cfg["session"], "chatId": chat_id, "text": body},
                headers=headers, timeout=30,
            )
            try:
                data = resp.json()
            except ValueError:
                data = {}
            if resp.status_code >= 400 or data.get("error"):
                detail = data.get("error") or (resp.text or "")[:200]
                rec.write({"status": "error", "error": detail})
                raise UserError(_("WAHA devolvio un error: %s") % detail)
            ext = data.get("id") or (data.get("_data") or {}).get("id") or False
            rec.write({"status": "sent", "external_id": ext})
        except UserError:
            raise
        except Exception as exc:  # noqa: BLE001
            _logger.exception("WAHA sendText")
            rec.write({"status": "error", "error": str(exc)[:200]})
            raise UserError(_("No se pudo contactar a WAHA en %s: %s") % (cfg["url"], exc)) from exc
        return rec

    # ------------------------------------------------------------------
    # Webhook (llamado por WAHA)
    # ------------------------------------------------------------------
    @api.model
    def _register_incoming(self, payload):
        p = payload.get("payload") or payload or {}
        chat_id = p.get("from") or p.get("chatId") or ""
        digits = "".join(c for c in str(chat_id).split("@")[0] if c.isdigit())
        partner = self.env["res.partner"]
        if digits:
            partner = self.env["res.partner"].search([("phone", "ilike", digits)], limit=1)
        ext_id = p.get("id") or p.get("timestamp")
        if ext_id:
            existing = self.sudo().search([("external_id", "=", str(ext_id))], limit=1)
            if existing:
                return existing
        rec = self.sudo().create({
            "partner_id": partner.id if partner else False,
            "direction": "in",
            "body": p.get("body") or p.get("preview") or "",
            "chat_id": chat_id,
            "status": "received",
            "external_id": str(ext_id) if ext_id else False,
        })
        if partner:
            # historial visible en la ficha del contacto (W3).
            # En rutas auth=none env.user queda vacio y message_post truena en
            # _is_public(); se postea con un usuario real (admin).
            try:
                env_user = api.Environment(
                    self.env.cr, self.env.ref("base.user_admin").id, {})
                partner.with_env(env_user).message_post(
                    body="WhatsApp entrante: %s" % (rec.body or "-"),
                    message_type="notification",
                    subtype_xmlid="mail.mt_note",
                )
            except Exception:  # noqa: BLE001
                _logger.exception("WhatsApp chatter")
        return rec
