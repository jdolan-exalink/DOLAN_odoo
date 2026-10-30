from odoo import http
from odoo.http import request

from ..models.dashboard import kpis

PAGE = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/><title>DOLAN — Mantenimiento</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/></head>
<body style="font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#1f2937">
<a href="/odoo" style="position:fixed;top:14px;left:16px;z-index:20;display:inline-flex;align-items:center;gap:6px;text-decoration:none;color:#4338ca;background:#fff;border:1px solid #e5e7eb;border-radius:999px;padding:7px 14px;font-family:system-ui,sans-serif;font-size:13px;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,.06)">&#8592; Volver a Odoo</a>
<div style="max-width:900px;margin:32px auto;padding:0 16px">
  <h3 style="margin:0 0 14px">Mantenimiento — Tablero</h3>
  <div id="kpis" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px"></div>
  <p style="color:#6b7280;font-size:12px;margin-top:18px">DOLAN_mantenimiento v1 — datos en vivo vía ORM.</p>
</div>
<script>
fetch("/dolan_mantenimiento/kpi", {method:"POST", headers:{"Content-Type":"application/json"},
  body:JSON.stringify({jsonrpc:"2.0",method:"call",params:{}}), credentials:"same-origin"})
 .then(r=>r.json()).then(j=>{
  const d=(j.result||{}).data||{};
  const cards=[["OT abiertas",d.ot_abiertas],["Críticas",d.ot_criticas],["Atrasadas",d.ot_atrasadas],
    ["Próx. 7 días",d.ot_proximas_7d],["Equipos",d.equipos]];
  document.getElementById("kpis").innerHTML=cards.map(([t,v])=>
    '<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px">'+
    '<div style="font-size:26px;font-weight:800">'+(v??0)+'</div>'+
    '<div style="color:#6b7280;font-size:12px">'+t+'</div></div>').join("");
 });
</script></body></html>"""


class DolanMantenimiento(http.Controller):

    @http.route("/dolan_mantenimiento", type="http", auth="user", methods=["GET"], csrf=False, sitemap=False)
    def page(self, **kw):
        if not request.env.user.has_group("base.group_system"):
            return request.make_response("solo administradores", status=403)
        return request.make_response(PAGE, headers=[("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])

    @http.route("/dolan_mantenimiento/kpi", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def kpi(self, **kw):
        if not request.env.user.has_group("base.group_system"):
            return {"error": "no_autorizado"}
        try:
            return {"data": kpis(request.env)}
        except Exception as exc:  # noqa: BLE001
            return {"error": exc.__class__.__name__}
