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
  <div style="display:flex;gap:10px;margin-top:12px">
    <a id="btn-op" href="#" style="flex:1;text-align:center;background:#714b67;color:#fff;padding:10px;border-radius:8px;text-decoration:none">Operaciones</a>
    <a id="btn-inv" href="#" style="flex:1;text-align:center;border:1px solid #d1d5db;padding:10px;border-radius:8px;text-decoration:none;color:#1f2937">Contar inventario</a>
  </div>
  <ul style="color:#6b7280;font-size:13px;margin-top:14px;padding-left:18px">
    <li>Escaneá un <b>producto</b> o su embalaje para localizarlo</li>
    <li>Escaneá una <b>recolección</b> (picking) para abrirla</li>
    <li>Escaneá un <b>contacto</b> (ref) para ver sus transferencias</li>
    <li>Escaneá un <b>tipo de operación</b> (ej. IN) para iniciar</li>
  </ul>
  <div id="out" style="margin-top:16px"></div>
</div>
<script>
const input=document.getElementById("scan"), out=document.getElementById("out");
function render(d){
 if(!d.ok){out.innerHTML='<div style="color:#dc2626;font-weight:700">No encontrado: '+(d.code||d.error||"")+'</div>';return;}
 const abrir = d.action_id ? '<a href="/odoo/action-'+d.action_id+'" style="display:inline-block;margin-top:10px;background:#714b67;color:#fff;padding:8px 16px;border-radius:8px;text-decoration:none">Abrir</a>' : "";
 let extra="";
 if(d.tipo==="producto" && d.existencias){
  const rows=Object.entries(d.existencias).map(([loc,q])=>'<tr><td style="padding:5px 8px;border-bottom:1px solid #e5e7eb">'+loc+'</td><td style="padding:5px 8px;text-align:right;font-weight:700;border-bottom:1px solid #e5e7eb">'+q+'</td></tr>').join("");
  extra='<table style="width:100%;margin-top:8px;font-size:13px;border-collapse:collapse">'+rows+'</table>';
 }
 const icono = d.tipo==="producto"?"▦":(d.tipo==="picking"?"⇄":(d.tipo==="partner"?"☺":"⚙"));
 out.innerHTML='<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:16px">'+
  '<div style="font-size:13px;color:#6b7280">'+icono+' '+d.tipo.toUpperCase()+'</div>'+
  '<div style="font-size:18px;font-weight:800">'+d.titulo+'</div>'+
  '<div style="color:#6b7280;font-size:13px">'+(d.detalle||"")+'</div>'+extra+abrir+'</div>';
}
function scan(){
 const code=input.value.trim(); if(!code)return;
 fetch("/dolan_codigo_barras/lookup",{method:"POST",headers:{"Content-Type":"application/json"},
  body:JSON.stringify({jsonrpc:"2.0",method:"call",params:{code}}),credentials:"same-origin"})
 .then(r=>r.json()).then(j=>render(j.result||{}));
 input.select();
}
input.addEventListener("keydown",e=>{if(e.key==="Enter")scan();});
fetch("/dolan_codigo_barras/modes",{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({jsonrpc:"2.0",method:"call",params:{}}),credentials:"same-origin"})
.then(r=>r.json()).then(j=>{const m=j.result||{};
 const b1=document.getElementById("btn-op"), b2=document.getElementById("btn-inv");
 if(m.operaciones)b1.href="/odoo/action-"+m.operaciones;
 if(m.inventario)b2.href="/odoo/action-"+m.inventario;});
</script><script type="text/javascript" src="/DOLAN_ai/static/src/js/embed_rail.js?v=32"></script></body></html>"""


class DolanCodigoBarras(http.Controller):

    @http.route("/dolan_codigo_barras/modes", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def modes(self, **kw):
        A = request.env["ir.actions.act_window"].sudo()
        def best(model):
            act = A.search([("res_model", "=", model), ("type", "ilike", "act_window")], order="id", limit=1)
            return act.id if act else False
        return {"operaciones": best("stock.picking"), "inventario": best("stock.quant")}

    @http.route("/dolan_codigo_barras", type="http", auth="user", methods=["GET"], csrf=False, sitemap=False)
    def page(self, **kw):
        return request.make_response(PAGE, headers=[("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])

    @http.route("/dolan_codigo_barras/lookup", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def do_lookup(self, **kw):
        try:
            return lookup(request.env, str(kw.get("code", "")))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": exc.__class__.__name__}
