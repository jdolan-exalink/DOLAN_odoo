"""Agentes DOLAN (S3): registro + tool-loop sobre ORM con permisos acotados.

Reglas de seguridad (ítem 2):
- Herramientas en allowlist estricta: search_read (lectura) y create
  (escritura limitada) SOLO en modelos habilitados por agente.
- Prohibido unlink/write fuera de allowlist de escritura.
- Máximo de iteraciones y límites de registros por llamada.
- Log de uso en chatter del agente (sin tokens ni contenido sensible).
"""
import json


from odoo import fields, models, _


class DolanAiAgente(models.Model):
    _name = "dolan.ai.agente"
    _description = "Agente DOLAN (IA)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True)
    proposito = fields.Text(string="Instrucciones", help="System-style prompt del agente (estilo EE: instrucciones + estilo de trabajo)")
    sugerencias = fields.Text(string="Sugerencias (una por línea)",
                              default="¿Cuántos registros hay?\nBuscá los últimos 5\nResumí lo que veas")
    modelos_ids = fields.Many2many("ir.model", string="Modelos autorizados",
                                   domain=[("transient", "=", False)])
    activo = fields.Boolean(default=True)

    def run(self, user_text, conversacion=None):
        """Ejecuta el loop del agente; con conversación => historial multi-turno."""
        self.ensure_one()
        if not self.activo:
            return {"done": True, "reply": None, "error": "agente_inactivo"}
        from . import agentes
        return agentes.loop_run(self.env, self, user_text, conversacion=conversacion)


class DolanAiConversacion(models.Model):
    _name = "dolan.ai.conversacion"
    _description = "Conversacion de agente DOLAN (IA)"
    _order = "write_date desc, id desc"

    name = fields.Char(required=True)
    agente_id = fields.Many2one("dolan.ai.agente", required=True, ondelete="cascade")
    user_id = fields.Many2one("res.users", default=lambda s: s.env.uid, required=True)
    mensaje_ids = fields.One2many("dolan.ai.mensaje", "conversacion_id", string="Mensajes")

    def name_get(self):
        return [(c.id, c.name or _("Nueva conversacion")) for c in self]


class DolanAiMensaje(models.Model):
    _name = "dolan.ai.mensaje"
    _description = "Mensaje de conversacion DOLAN (IA)"
    _order = "id"

    conversacion_id = fields.Many2one("dolan.ai.conversacion", required=True, ondelete="cascade")
    rol = fields.Selection([("user", "Usuario"), ("assistant", "Agente"), ("tool", "Herramienta")],
                           required=True, default="user")
    content = fields.Text(required=True)

MAX_ITER = 3
MAX_LIMIT = 20
ALLOWED_TOOLS = ("search_read", "search_count", "read", "create", "write")
WRITE_MODELS_LIMIT = {"res.partner", "crm.lead", "project.project"}


class AgenteLoop:
    def __init__(self, env, agente, conversacion=None):
        self.env = env
        self.agente = agente
        self.conversacion = conversacion
        self.history = []
        self.turns = []  # [{role, content}] para multi-turno
        if conversacion:
            for m in conversacion.mensaje_ids[-12:]:
                if m.rol in ("user", "assistant"):
                    self.turns.append({"role": m.rol, "content": m.content})

    def tool_spec(self):
        return [
            {"name": "search_read", "desc": "Buscar registros: model, domain(list), fields(list), limit<=20",
             "args": ["model", "domain", "fields", "limit"]},
            {"name": "search_count", "desc": "Contar registros: model, domain(list)",
             "args": ["model", "domain"]},
            {"name": "read", "desc": "Leer por ids: model, ids(list), fields(list)",
             "args": ["model", "ids", "fields"]},
            {"name": "create", "desc": "Crear registro: model en lista de escritura, vals dict",
             "args": ["model", "vals"]},
            {"name": "write", "desc": "Escribir campos permitidos: model, ids(list), vals dict (solo campos blancos)",
             "args": ["model", "ids", "vals"]},
        ]

    WRITE_FIELDS_LIMIT = {
        "res.partner": {"name", "email", "phone", "mobile", "street", "city", "comment", "ref"},
        "crm.lead": {"name", "description", "probability", "priority"},
        "project.project": {"name", "description"},
    }

    def _filter_write_fields(self, model, vals):
        """Solo campos de la allowlist del modelo; nunca unlink ni campos sensibles."""
        if not isinstance(vals, dict):
            raise ValueError("vals_invalidos")
        allowed = self.WRITE_FIELDS_LIMIT.get(model, set())
        bad = set(vals) - allowed
        if bad:
            raise ValueError("campos_no_permitidos: " + ",".join(sorted(bad))[:120])
        return {k: v for k, v in vals.items() if k in allowed}

    def _check_model(self, model, write=False):
        if not isinstance(model, str) or "." not in model:
            raise ValueError("modelo_invalido")
        if model not in self.agente.modelos_ids.mapped("model"):
            raise ValueError("modelo_no_autorizado")
        if write and model not in WRITE_MODELS_LIMIT:
            raise ValueError("escritura_no_permitida_en_este_modelo")

    def run_tool(self, name, args):
        if name not in ALLOWED_TOOLS:
            return {"error": "herramienta_no_autorizada"}
        try:
            if name == "search_read":
                self._check_model(args.get("model"))
                limit = min(int(args.get("limit") or 10), MAX_LIMIT)
                domain = args.get("domain") or []
                if not isinstance(domain, list):
                    raise ValueError("dominio_invalido")
                fields = [f for f in (args.get("fields") or []) if isinstance(f, str)][:15]
                recs = self.env[args.get("model")].sudo().search_read(domain, fields, limit=limit)
                return {"result": recs}
            if name == "search_count":
                self._check_model(args.get("model"))
                domain = args.get("domain") or []
                if not isinstance(domain, list):
                    raise ValueError("dominio_invalido")
                return {"result": {"count": self.env[args.get("model")].sudo().search_count(domain)}}
            if name == "read":
                self._check_model(args.get("model"))
                ids = args.get("ids") or []
                if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids) or len(ids) > MAX_LIMIT:
                    raise ValueError("ids_invalidos")
                fields = [f for f in (args.get("fields") or []) if isinstance(f, str)][:15]
                recs = self.env[args.get("model")].sudo().browse(ids).read(fields)
                return {"result": recs}
            if name == "create":
                self._check_model(args.get("model"), write=True)
                vals = self._filter_write_fields(args.get("model"), args.get("vals") or {})
                rec = self.env[args.get("model")].sudo().create(vals)
                return {"result": {"id": rec.id}}
            if name == "write":
                self._check_model(args.get("model"), write=True)
                ids = args.get("ids") or []
                if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids) or len(ids) > MAX_LIMIT:
                    raise ValueError("ids_invalidos")
                vals = self._filter_write_fields(args.get("model"), args.get("vals") or {})
                self.env[args.get("model")].sudo().browse(ids).write(vals)
                return {"result": {"written": len(ids)}}
        except ValueError as exc:
            return {"error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            return {"error": exc.__class__.__name__}

    def step(self, user_text):
        """Una pasada del loop: pide JSON de acción al modelo; ejecuta 1 tool.
        Los resultados de herramientas previas se adjuntan al prompt para que
        el modelo pueda cerrar con reply."""
        from . import chatgpt_oauth as cgo
        tokens = cgo.get_valid_tokens()
        if not tokens:
            return {"done": False, "reply": None, "error": "no_conectado"}
        if tokens.get("needs_reconnect"):
            return {"done": False, "reply": None, "error": "token_vencido_reconectar"}
        import requests
        spec = json.dumps(self.tool_spec(), ensure_ascii=False)
        modelos = ", ".join(self.agente.modelos_ids.mapped("model"))
        previo = ""
        if self.history:
            previo = " Resultados de herramientas anteriores: " + json.dumps(self.history[-2:], ensure_ascii=False)[:800] + " Usá esos resultados y respondé con {\"reply\": ...} si ya tenés la respuesta."
        prompt = (
            f"Sos el agente '{self.agente.name}'. Herramientas: {spec}. "
            f"Modelos autorizados: {modelos}. "
            "Respondé SOLO JSON: {\"tool\": \"search_read|create\", \"args\": {...}} "
            "o {\"reply\": \"respuesta final\"}." + previo + " Pregunta: " + user_text[:400]
        )
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        if tokens.get("account_id"):
            headers["ChatGPT-Account-Id"] = tokens["account_id"]
        # multi-turno: instrucciones + turnos previos de la conversación + turno actual
        instrucciones = (self.agente.proposito or "").strip()
        msgs = []
        if instrucciones:
            msgs.append({"role": "system", "content": [{"type": "input_text", "text": instrucciones[:2000]}]})
        # los turnos assistant usan output_text (contrato Responses API);
        # user/system usan input_text
        for t in self.turns:
            if t.get("role") not in ("user", "assistant"):
                continue
            ctype = "output_text" if t["role"] == "assistant" else "input_text"
            msgs.append({"role": t["role"], "content": [{"type": ctype, "text": t["content"][:1500]}]})
        msgs.append({"role": "user", "content": [{"type": "input_text", "text": prompt}]})
        body = {
            "model": "gpt-6-luna",
            "input": msgs,
            "max_output_tokens": 500,
            "stream": True,
            "store": False,
        }
        try:
            resp = requests.post(cgo.CODEX_API_ENDPOINT, json=body,
                                 headers=headers, timeout=(15, 180), stream=True)
        except requests.RequestException:
            return {"done": False, "reply": None, "error": "http_request_exception"}
        if resp.status_code not in (200, 201):
            return {"done": False, "reply": None, "error": f"http_{resp.status_code}"}
        parts = []
        try:
            for raw in resp.iter_lines():
                if not raw:
                    continue
                line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if not payload or payload == "[DONE]":
                    continue
                try:
                    ev = json.loads(payload)
                except ValueError:
                    continue
                etype = ev.get("type", "")
                if etype == "response.output_text.delta":
                    parts.append(ev.get("delta", ""))
                elif etype == "response.output_text.done" and ev.get("text"):
                    parts = [ev["text"]]
                elif etype in ("response.failed", "response.incomplete"):
                    return {"done": False, "reply": None, "error": "stream_failed"}
        except (requests.RequestException, OSError):
            return {"done": False, "reply": None, "error": "stream_error"}
        text = "".join(parts)
        try:
            m = json.loads(text[text.index("{"): text.rindex("}") + 1])
        except (ValueError, AttributeError):
            return {"done": True, "reply": text[:600], "tool": None}
        if m.get("reply"):
            return {"done": True, "reply": m["reply"][:600], "tool": None}
        tool = m.get("tool")
        result = self.run_tool(tool, m.get("args") or {})
        self.history.append({"tool": tool, "result": result})
        self.agente.message_post(body=f"tool={tool} ok={'error' not in result}")
        return {"done": False, "tool_result": result, "reply": None}


def loop_run(env, agente, user_text, max_iter=MAX_ITER, conversacion=None):
    loop = AgenteLoop(env, agente, conversacion=conversacion)
    if conversacion:
        env["dolan.ai.mensaje"].sudo().create({"conversacion_id": conversacion.id, "rol": "user", "content": user_text[:2000]})
    final = None
    for _ in range(max_iter):
        step = loop.step(user_text)
        if step.get("error"):
            if conversacion:
                env["dolan.ai.mensaje"].sudo().create({"conversacion_id": conversacion.id, "rol": "assistant", "content": f"error: {step['error']}"})
            return step
        if step.get("tool_result"):
            loop.turns.append({"role": "assistant", "content": f"tool_result: {json.dumps(step['tool_result'], ensure_ascii=False)[:1000]}"})
            if conversacion:
                env["dolan.ai.mensaje"].sudo().create({"conversacion_id": conversacion.id, "rol": "tool", "content": json.dumps(step["tool_result"], ensure_ascii=False)[:1000]})
        if step.get("done"):
            final = step
            break
    if final is None:
        final = {"done": True, "reply": None, "error": "max_iteraciones"}
    if conversacion and final.get("reply"):
        env["dolan.ai.mensaje"].sudo().create({"conversacion_id": conversacion.id, "rol": "assistant", "content": final["reply"]})
    return final
