from odoo import http
from odoo.http import request

from ..models.dashboard import kpis

PAGE = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/><title>DOLAN — Flotilla</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/></head>
<body style="font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#1f2937">
<div style="max-width:900px;margin:32px auto;padding:0 16px">
  <h3 style="margin:0 0 14px">Flotilla — Tablero</h3>
  <div id="kpis" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px"></div>
  <p style="color:#6b7280;font-size:12px;margin-top:18px">DOLAN_flotilla v1 — alertas de contratos y costos del mes.</p>
</div>
<script>
fetch("/dolan_flotilla/kpi",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({jsonrpc:"2.0",method:"call",params:{}}),credentials:"same-origin"})
.then(r=>r.json()).then(j=>{const d=(j.result||{}).data||{};
 const cards=[["Vehículos",d.vehiculos],["Contratos 30 días",d.contratos_por_vencer_30d],["Vencidos",d.contratos_vencidos],
  ["Contratos mes","$"+Number(d.costo_contratos_mes||0).toLocaleString("es-AR")],["Services mes","$"+Number(d.costo_services_mes||0).toLocaleString("es-AR")]];
 document.getElementById("kpis").innerHTML=cards.map(([t,v])=>
  '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px">'+
  '<div style="font-size:24px;font-weight:800">'+(v??0)+'</div>'+
  '<div style="color:#6b7280;font-size:12px">'+t+'</div></div>').join("");});
</script><script type="text/javascript" src="/DOLAN_ai/static/src/js/embed_rail.js?v=32"></script></body></html>"""


class DolanFlotilla(http.Controller):

    @http.route("/dolan_flotilla", type="http", auth="user", methods=["GET"], csrf=False, sitemap=False)
    def page(self, **kw):
        if not request.env.user.has_group("base.group_system"):
            return request.make_response("solo administradores", status=403)
        return request.make_response(PAGE, headers=[("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])

    @http.route("/dolan_flotilla/kpi", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def kpi(self, **kw):
        if not request.env.user.has_group("base.group_system"):
            return {"error": "no_autorizado"}
        try:
            return {"data": kpis(request.env)}
        except Exception as exc:  # noqa: BLE001
            return {"error": exc.__class__.__name__}
