from odoo import http
from odoo.http import request

from ..models.dashboard import kpis

PAGE = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"/><title>DOLAN Suscripciones</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/></head>
<body style="font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#1f2937">
<div style="max-width:860px;margin:28px auto;padding:0 16px">
  <h3 style="margin:0 0 14px">Suscripciones — MRR</h3>
  <div id="kpis" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px"></div>
  <p style="color:#6b7280;font-size:12px;margin-top:16px">Patrón EE: MRR, activas, próximas 7 días, por facturar (períodos vencidos por el cron).</p>
</div>
<script>
fetch("/dolan_suscripciones/kpi",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({jsonrpc:"2.0",method:"call",params:{}}),credentials:"same-origin"})
.then(r=>r.json()).then(j=>{const d=(j.result||{}).data||{};
 const f=n=>Number(n||0).toLocaleString("es-AR",{maximumFractionDigits:2});
 const cards=[["MRR $",f(d.mrr)],["Activas",d.activas],["Próx. 7 días",d.proximas_7d],
  ["Por facturar",d.por_facturar],["Planes",d.planes]];
 document.getElementById("kpis").innerHTML=cards.map(([t,v])=>
  '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px;text-align:center">'+
  '<div style="font-size:24px;font-weight:800">'+(v??0)+'</div><div style="color:#6b7280;font-size:12px">'+t+'</div></div>').join("");});
</script><script type="text/javascript" src="/DOLAN_ai/static/src/js/embed_rail.js?v=31"></script></body></html>"""


class DolanSuscripciones(http.Controller):

    @http.route("/dolan_suscripciones", type="http", auth="user", methods=["GET"], csrf=False, sitemap=False)
    def page(self, **kw):
        if not request.env.user.has_group("base.group_system"):
            return request.make_response("solo administradores", status=403)
        return request.make_response(PAGE, headers=[("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])

    @http.route("/dolan_suscripciones/kpi", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def kpi(self, **kw):
        if not request.env.user.has_group("base.group_system"):
            return {"error": "no_autorizado"}
        try:
            return {"data": kpis(request.env)}
        except Exception as exc:  # noqa: BLE001
            return {"error": exc.__class__.__name__}
