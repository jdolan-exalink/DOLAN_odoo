from odoo import http
from odoo.http import request

from ..models import matching

PAGE = """<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"/><title>DOLAN Bancos</title>
<meta name="viewport" content="width=device-width, initial-scale=1"/></head>
<body style="font-family:system-ui,sans-serif;margin:0;background:#f6f7f9;color:#1f2937">
<div style="max-width:900px;margin:28px auto;padding:0 16px">
  <h3 style="margin:0 0 14px">Conciliación de bancos</h3>
  <div id="kpis" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px"></div>
  <div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px">
    <b>Importar extracto (CSV)</b>
    <p style="font-size:12.5px;color:#6b7280;margin:6px 0">Columnas: <code>fecha,referencia,debito,credito[,partner]</code> — fecha AAAA-MM-DD. Punto como miles, coma como decimal.</p>
    <textarea id="csv" rows="6" style="width:100%;font-family:monospace;font-size:12px"></textarea>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button id="btn-import" type="button">Importar</button>
      <button id="btn-run" type="button">Conciliar automáticamente</button>
    </div>
    <div id="out" style="margin-top:10px;font-size:13px"></div>
  </div>
  <p style="color:#6b7280;font-size:12px;margin-top:14px">Matching: partner + importe residual exacto. Ambiguo => queda para conciliación manual.</p>
</div>
<script>
function rpc(p,params){return fetch(p,{method:"POST",headers:{"Content-Type":"application/json"},
 body:JSON.stringify({jsonrpc:"2.0",method:"call",params:params||{}}),credentials:"same-origin"})
 .then(r=>r.json()).then(j=>j.result||j.error||{error:"rpc"});}
function pintar(d){document.getElementById("kpis").innerHTML=
 [["Pendientes",d.pendientes],["Conciliadas hoy",d.conciliadas_hoy],["Importadas hoy",d.importadas_hoy]]
 .map(([t,v])=>'<div style="background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px;text-align:center">'+
 '<div style="font-size:24px;font-weight:800">'+(v??0)+'</div><div style="color:#6b7280;font-size:12px">'+t+'</div></div>').join("");}
function refresh(){rpc("/dolan_bancos/kpi").then(d=>d.data&&pintar(d.data));}
document.getElementById("btn-import").addEventListener("click",()=>{
 const txt=document.getElementById("csv").value;
 rpc("/dolan_bancos/importar",{csv:txt}).then(d=>{
  document.getElementById("out").innerHTML = d.ok
    ? '<span style="color:#16a34a;font-weight:700">Importadas '+d.lineas+' líneas</span>'
    : '<span style="color:#dc2626">Error: '+(d.detalle||d.error)+'</span>';
  refresh();});});
document.getElementById("btn-run").addEventListener("click",()=>{
 document.getElementById("out").innerHTML="<i>Conciliando…</i>";
 rpc("/dolan_bancos/conciliar").then(d=>{
  document.getElementById("out").innerHTML = d.error
    ? '<span style="color:#dc2626">Error: '+(d.detalle||d.error)+'</span>'
    : '<span style="color:#16a34a;font-weight:700">Conciliadas '+d.conciliadas+' · ambiguas '+d.ambiguas+' · sin candidato '+d.sin_candidato+'</span>';
  refresh();});});
refresh();
</script></body></html>"""


class DolanBancos(http.Controller):

    @http.route("/dolan_bancos", type="http", auth="user", methods=["GET"], csrf=False, sitemap=False)
    def page(self, **kw):
        if not request.env.user.has_group("account.group_account_invoice"):
            return request.make_response("solo contabilidad", status=403)
        return request.make_response(PAGE, headers=[("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")])

    @http.route("/dolan_bancos/kpi", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def kpi(self, **kw):
        from datetime import date, timedelta
        desde = (date.today() - timedelta(days=90)).isoformat()
        St = request.env["account.bank.statement.line"].sudo()
        pendientes = St.search_count([("is_reconciled", "=", False), ("date", ">=", desde)])
        conc_hoy = St.search_count([("is_reconciled", "=", True), ("date", ">=", date.today().isoformat())])
        return {"data": {"pendientes": pendientes, "conciliadas_hoy": conc_hoy, "importadas_hoy": pendientes + conc_hoy}}

    @http.route("/dolan_bancos/importar", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def importar(self, **kw):
        if not request.env.user.has_group("account.group_account_invoice"):
            return {"ok": False, "error": "no_autorizado"}
        try:
            return matching.importar_extracto(request.env, str(kw.get("csv") or ""))
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": exc.__class__.__name__, "detalle": str(exc)[:200]}

    @http.route("/dolan_bancos/conciliar", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def conciliar(self, **kw):
        if not request.env.user.has_group("account.group_account_invoice"):
            return {"ok": False, "error": "no_autorizado"}
        try:
            return matching.conciliar(request.env)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": exc.__class__.__name__, "detalle": str(exc)[:200]}
