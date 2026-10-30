import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class DolanWhatsappController(http.Controller):
    """Webhook de WAHA.

    type=http para poder resolver la BD con ?db= (las rutas jsonrpc con
    auth=none no resuelven la BD desde params). Protegido con ?token=
    si esta configurado en dolan.waha.webhook_token.
    """

    @http.route("/dolan_waha/webhook", type="http", auth="none", csrf=False,
                methods=["POST"], save_session=False)
    def webhook(self, **kw):
        token = (kw or {}).get("token") or request.httprequest.args.get("token")
        message_model = request.env["dolan.whatsapp.message"]
        cfg = message_model._waha_config()
        if cfg["token"] and token != cfg["token"]:
            return request.make_json_response({"ok": False, "error": "token_invalido"})
        try:
            body = request.get_jsonrequest() or {}
        except Exception:  # noqa: BLE001
            body = {}
        params = body.get("params") if isinstance(body.get("params"), dict) else body
        payload = (params or {}).get("payload") or {}
        try:
            rec = message_model.sudo()._register_incoming(payload)
            return request.make_json_response({"ok": True, "id": rec.id})
        except Exception as exc:  # noqa: BLE001
            _logger.exception("WAHA webhook")
            return request.make_json_response({"ok": False, "error": str(exc)[:200]})
