from odoo import http
from odoo.http import request

from ..models.lookup import lookup

PAGE = """<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"/><title>DOLAN — Escaneo</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/></head>
<body style="font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#1f2937">
<div style="max-width:760px;margin:28px auto;padding:0 16px">
  <h3 style="margin:0 0 12px">Escaneo de codigos</h3>
  <input id="scan" autofocus placeholder="Escanea o tipea el codigo y Enter"
    style="width:100%;font-size:22px;padding:14px;border:2px solid #714b67;border-radius:10px;box-sizing:border-box"/>
  <div id="out" style="margin-top:16px"></div>
</div>
<script>
const input=document.getElementById("scan"), out=document.getElementById("out");
input.addEventListener("keydown",e=>{
 if(e.key!=="Enter")return;
 const code=input.value.trim(); if(!code)return;
 fetch("/dolan_codigo_barras/lookup",{method:"POST",headers:{"Content-Type":"application/json"},
  body:JSON.stringify({jsonrpc:"2.0",method:"call",params:{code}}),credentials:"same-origin"})
 .then(r=>r.json()).then(j=>{
  const d=j.result||{};
  if(!d.ok){out.innerHTML='<div style="color:#dc2626;font-weight:700">No encontrado: '+(d.code||d.error||"")+'</div>';return;}
  const rows=Object.entries(d.existencias||{}).map(([loc,q])=>
   '<tr><td style="padding:6px 10px;border-bottom:1px solid #e5e7eb">'+loc+'</td>'+
   '<td style="padding:6px 10px;border-bottom:1px solid #e5e7eb;text-align:right;font-weight:700">'+q+'</td></tr>').join("");
  out.innerHTML='<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px">'+
   '<div style="font-size:18px;font-weight:800">'+d.producto.name+'</div>'+
   '<div style="color:#6b7280;font-size:13px">SKU: '+(d.producto.sku||"—")+' · Barras: '+(d.producto.barcode||"—")+
   ' · Total: <b>'+d.total+'</b> '+d.producto.unidad+'</div>'+
   '<table style="width:100%;margin-top:10px;font-size:14px;border-collapse:collapse">'+rows+'</table></div>';
 });
 input.select();
});
</script></body></html>"""


class DolanCodigoBarras(http.Controller):

    @http.route("/dolan_codigo_barras", type="http", auth="user", methods=["GET"], csrf=False, sitemap=False)
    def page(self, **kw):
        return request.make_response(PAGE, headers=[("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])

    @http.route("/dolan_codigo_barras/lookup", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def do_lookup(self, **kw):
        try:
            return lookup(request.env, str(kw.get("code", "")))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": exc.__class__.__name__}
