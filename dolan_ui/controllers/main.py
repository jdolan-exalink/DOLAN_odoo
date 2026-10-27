from odoo import http
from odoo.http import request


class DolanUiController(http.Controller):

    @http.route("/web/dolan_ui/config", type="jsonrpc", auth="user", readonly=True)
    def dolan_ui_config(self):
        return request.env["dolan.ui.settings"].sudo().get_public_config()
