"""F2 — PRD04: central global search over the models the roles need,
respecting record permissions (search applies record rules automatically)."""
import logging

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError

_log = logging.getLogger(__name__)

# model, UI label, searchable fields
TARGETS = [
    ("res.partner", "Contactos", ["name", "email", "vat", "phone"]),
    ("product.product", "Productos", ["name", "default_code", "barcode"]),
    ("account.move", "Comprobantes", ["name", "ref"]),
    ("sale.order", "Pedidos", ["name"]),
    ("stock.picking", "Remitos", ["name"]),
    ("account.payment", "Pagos", ["name"]),
    ("maintenance.equipment", "Equipos", ["name"]),
    ("mrp.production", "Produccion", ["name"]),
]
PER_MODEL = 4


class DolanGlobalSearch(http.Controller):

    @http.route("/dolan/global_search", type="jsonrpc", auth="user")
    def global_search(self, query="", limit=12):
        query = (query or "").strip()
        if len(query) < 2:
            return {"results": []}
        env = request.env
        out = []
        for model, label, fields in TARGETS:
            if len(out) >= limit:
                break
            if model not in env.registry:
                continue
            # OR across fields: a bare list would AND them and never match
            domain = ["|"] * (len(fields) - 1) + [(f, "ilike", query) for f in fields]
            try:
                recs = env[model].search(
                    domain,
                    limit=PER_MODEL, order="write_date desc")
            except AccessError:
                continue
            except Exception:
                _log.exception("dolan global_search: %s", model)
                continue
            for rec in recs:
                out.append({
                    "model": model,
                    "id": rec.id,
                    "label": label,
                    "title": (rec.display_name or "")[:90],
                })
        return {"results": out[:limit]}
