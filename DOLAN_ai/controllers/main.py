import os
import re

from odoo import http
from odoo.http import request

from ..models import chatgpt_oauth as ai
from ..models import ocr as ai_ocr

PAGE_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <title>DOLAN AI — ChatGPT</title>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
</head>
<body style="font-family: system-ui, sans-serif; margin: 0; background: #f6f7f9; color: #1f2937;">
  <div style="max-width: 780px; margin: 40px auto; padding: 0 16px;">
    <h3 style="margin: 0 0 4px;">DOLAN AI — ChatGPT (OAuth)</h3>
    <p style="color: #6b7280; font-size: 13px; margin-top: 0;">
      Conexion directa con tu cuenta ChatGPT estilo opencode/pi (device flow).
      Los tokens se guardan solo en archivo local 0600, nunca en la base de datos.
    </p>
    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
      <span id="dolan-ai-status" class="badge">Sin conexion</span>
      <div style="margin-left: auto; display: flex; gap: 8px;">
        <button id="dolan-ai-connect" type="button">Conectar ChatGPT</button>
        <button id="dolan-ai-test" type="button">Probar</button>
        <button id="dolan-ai-logout" type="button">Desconectar</button>
        <button id="dolan-ai-ocr" type="button">Escanear compra (IA)</button>
        <input id="dolan-ai-file" type="file" accept="image/*" style="display:none"/>
      </div>
    </div>
    <div id="dolan-ai-device" style="display: none; background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 16px;">
      <p style="margin: 0 0 6px; font-size: 13px; color: #6b7280;">Abris en cualquier navegador y autorizas con este codigo:</p>
      <a id="dolan-ai-uri" href="#" target="_blank" rel="noopener" style="font-weight: 700; color: #714b67;">auth.openai.com/codex/device</a>
      <div id="dolan-ai-code" style="font-family: monospace; font-size: 40px; letter-spacing: 4px; margin: 10px 0;">----</div>
      <p style="margin: 0; font-size: 13px; color: #6b7280;">El codigo vence en 15 minutos. Esta pagina verifica sola cada pocos segundos.</p>
    </div>
    <p style="color: #6b7280; font-size: 13px; margin-top: 22px;">
      El primer test luego de autorizar valida la llamada a
      <code>chatgpt.com/backend-api/codex/responses</code> con tu token.
      El botón <b>Escanear compra (IA)</b> sube una foto de factura y crea un
      borrador en Facturas de compra (previsualizá antes de confirmar).
    </p>
    <div id="dolan-ai-ocr-out" style="margin-top:12px"></div>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0"/>
  <h4 style="margin:0 0 8px">Agentes</h4>
  <div style="display:flex;gap:8px;align-items:center">
    <select id="dolan-ai-agente" style="padding:8px;border:1px solid #d1d5db;border-radius:8px"></select>
    <input id="dolan-ai-agente-text" placeholder="Pedí algo al agente…" style="flex:1;padding:9px;border:1px solid #d1d5db;border-radius:8px"/>
    <button id="dolan-ai-agente-run" type="button">Enviar</button>
  </div>
  <div id="dolan-ai-agente-out" style="margin-top:10px;font-size:14px"></div>
  </div>
  <style>
    .o_dolan_rail{position:fixed;top:0;left:0;bottom:0;width:240px;background:#fff;border-right:1px solid #e5e7eb;box-shadow:4px 0 16px rgba(15,23,42,.06);overflow-y:auto;padding:12px 0;z-index:30;display:flex;flex-direction:column}
    .o_dolan_rail_title{font-size:11px;text-transform:uppercase;letter-spacing:.08em;color:#6b7280;font-weight:700;padding:6px 16px 10px}
    .o_dolan_rail_item{display:flex;align-items:center;gap:10px;padding:9px 14px;margin:1px 8px;border-radius:8px;color:#1f2937;text-decoration:none}
    .o_dolan_rail_item:hover{background:#eef2ff;color:#4338ca}
    .o_dolan_rail_item img{width:24px;height:24px;border-radius:6px}
    .o_dolan_rail_item span{font-size:13.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    body{padding-left:240px !important}
    @media (max-width:992px){.o_dolan_rail{display:none}body{padding-left:0 !important}}
    .badge { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: #e5e7eb; }
    .bg-success { background: #16a34a !important; color: #fff; }
    .bg-danger { background: #dc2626 !important; color: #fff; }
    .bg-warning { background: #f59e0b !important; color: #111; }
    .bg-info { background: #0ea5e9 !important; color: #fff; }
    .bg-secondary { background: #e5e7eb !important; color: #374151; }
    button { border: 1px solid #d1d5db; background: #fff; border-radius: 8px; padding: 7px 14px; font-size: 14px; cursor: pointer; }
    button:hover { background: #f3f4f6; }
    #dolan-ai-connect { background: #714b67; border-color: #714b67; color: #fff; }
    #dolan-ai-connect:hover { background: #5d3d56; }
  </style>
  <script type="text/javascript" src="/DOLAN_ai/static/src/js/page.js"></script>
  <script type="text/javascript" src="/DOLAN_ai/static/src/js/ocr.js"></script>
  <script>
  (function(){
    fetch("/web/dataset/call_kw",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({jsonrpc:"2.0",method:"call",params:{model:"ir.ui.menu",method:"load_menus",args:[false],kwargs:{}}}),
      credentials:"same-origin"}).then(r=>r.json()).then(function(j){
      var tree=j.result||{}; var rail=document.createElement("div"); rail.className="o_dolan_rail";
      var t=document.createElement("div"); t.className="o_dolan_rail_title"; t.textContent="APLICACIONES"; rail.appendChild(t);
      var ids=Object.keys(tree).filter(function(k){return !isNaN(k);});
      ids.sort(function(a,b){return (tree[a].sequence||0)-(tree[b].sequence||0);});
      ids.forEach(function(k){ var m=tree[k];
        var a=document.createElement("a"); a.className="o_dolan_rail_item"; a.href="/odoo/action-"+(m.actionID||m.id);
        if(m.webIconData){var img=document.createElement("img"); img.src=m.webIconData; a.appendChild(img);}
        var sp=document.createElement("span"); sp.textContent=m.name; a.appendChild(sp);
        rail.appendChild(a);});
      document.body.appendChild(rail);});
  })();
  </script>
</body>
</html>"""

_STATIC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")


def _is_admin():
    return request.env.user.has_group("base.group_system")


class DolanAiController(http.Controller):

    @http.route("/dolan_ai", type="http", auth="user", methods=["GET"], csrf=False, sitemap=False)
    def page(self, **kwargs):
        if not _is_admin():
            return request.make_response("DOLAN AI: solo administradores", status=403)
        return request.make_response(PAGE_HTML,
                                     headers=[("Content-Type", "text/html; charset=utf-8"),
                                              ("Cache-Control", "no-store")])

    @http.route("/DOLAN_ai/static/src/js/<path:fname>", type="http", auth="public", methods=["GET"], csrf=False, sitemap=False)
    def static_js(self, fname, **kwargs):
        safe = os.path.normpath(fname).replace("\\", "/")
        if safe.startswith("..") or "/" in safe or not safe.endswith(".js"):
            return request.make_response("not found", status=404)
        path = os.path.join(_STATIC, "src", "js", safe)
        if not os.path.isfile(path):
            return request.make_response("not found", status=404)
        with open(path, "rb") as fh:
            data = fh.read()
        return request.make_response(
            data,
            headers=[("Content-Type", "application/javascript; charset=utf-8"),
                     ("Cache-Control", "no-store")],
        )

    def _rpc(self, fn, **kwargs):
        if not _is_admin():
            return {"error": "no_autorizado"}
        try:
            return fn(**kwargs)
        except Exception as exc:  # noqa: BLE001 — el error vuelve al front sin tokens
            return {"error": exc.__class__.__name__}

    @http.route("/dolan_ai/status", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def status_rpc(self, **kwargs):
        return self._rpc(ai.status)

    @http.route("/dolan_ai/start", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def start_rpc(self, **kwargs):
        return self._rpc(ai.start_device_flow)

    @http.route("/dolan_ai/poll", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def poll_rpc(self, **kwargs):
        return self._rpc(ai.poll_once)

    @http.route("/dolan_ai/logout", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def logout_rpc(self, **kwargs):
        return self._rpc(lambda: {"disconnected": ai.disconnect()})

    @http.route("/dolan_ai/test", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def test_rpc(self, **kwargs):
        def _run():
            prompt = str(kwargs.get("prompt") or "Responde solo: DOLAN_OK")
            prompt = re.sub(r"\s+", " ", prompt)[:200]
            return ai.ask(prompt)
        return self._rpc(_run)

    @http.route("/dolan_ai/ocr_scan", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def ocr_scan(self, **kwargs):
        """Imagen data-URL -> OCR -> vista previa / creacion de borrador."""
        if not _is_admin():
            return {"ok": False, "error": "no_autorizado"}
        data_url = str(kwargs.get("image") or "")
        commit = bool(kwargs.get("commit"))
        if not data_url.startswith("data:image/"):
            return {"ok": False, "error": "imagen_invalida"}
        if len(data_url) > ai_ocr.MAX_IMAGE_BYTES * 2:  # base64 ~4/3
            return {"ok": False, "error": "imagen_muy_grande"}
        try:
            res = ai_ocr.extract_from_image(request.env, data_url)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": exc.__class__.__name__}
        if not res.get("ok"):
            return res
        if not commit:
            mapped = ai_ocr.map_to_draft(request.env, res["datos"])
            return {**res, **mapped, "preview": True}
        try:
            created = ai_ocr.create_draft(request.env, res["datos"])
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": exc.__class__.__name__}
        return created

    @http.route("/dolan_ai/agente/run", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def agente_run(self, **kwargs):
        if not _is_admin():
            return {"ok": False, "error": "no_autorizado"}
        aid = kwargs.get("agente_id")
        text = str(kwargs.get("text") or "")[:500]
        if not text:
            return {"ok": False, "error": "texto_vacio"}
        try:
            agente = request.env["dolan.ai.agente"].browse(int(aid))
            if not agente.exists():
                return {"ok": False, "error": "agente_inexistente"}
            res = agente.run(text)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": exc.__class__.__name__}
        return res

    @http.route("/dolan_ai/agentes", type="jsonrpc", auth="user", methods=["POST"], csrf=False, sitemap=False)
    def agentes_list(self, **kwargs):
        if not _is_admin():
            return {"error": "no_autorizado"}
        Agent = request.env["dolan.ai.agente"].sudo()
        if not Agent.search_count([]):
            # seed: agente de contactos listo para usar
            partner_m = request.env["ir.model"].sudo().search([("model", "=", "res.partner")], limit=1)
            Agent.create({
                "name": "Asistente de contactos",
                "proposito": "Busca y crea contactos (res.partner) cuando se lo pedís.",
                "modelos_ids": [(6, 0, partner_m.ids)],
            })
        recs = Agent.search_read([], ["name", "id", "proposito"], limit=20)
        return {"agentes": recs}
