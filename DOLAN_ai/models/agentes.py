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
    proposito = fields.Text(string="Proposito")
    modelos_ids = fields.Many2many("ir.model", string="Modelos autorizados",
                                   domain=[("transient", "=", False)])
    activo = fields.Boolean(default=True)

    def run(self, user_text):
        """Ejecuta el loop del agente con el texto del usuario."""
        self.ensure_one()
        if not self.activo:
            return {"done": True, "reply": None, "error": "agente_inactivo"}
        from . import agentes
        return agentes.loop_run(self.env, self, user_text)

MAX_ITER = 5
MAX_LIMIT = 20
ALLOWED_TOOLS = ("search_read", "create")
WRITE_MODELS_LIMIT = {"res.partner", "crm.lead", "project.project"}


class AgenteLoop:
    def __init__(self, env, agente):
        self.env = env
        self.agente = agente
        self.history = []

    def tool_spec(self):
        return [
            {"name": "search_read", "desc": "Buscar registros: model, domain(list), fields(list), limit<=20",
             "args": ["model", "domain", "fields", "limit"]},
            {"name": "create", "desc": "Crear registro: model en lista blanca, vals dict",
             "args": ["model", "vals"]},
        ]

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
            if name == "create":
                self._check_model(args.get("model"), write=True)
                vals = args.get("vals") or {}
                if not isinstance(vals, dict):
                    raise ValueError("vals_invalidos")
                rec = self.env[args.get("model")].sudo().create(vals)
                return {"result": {"id": rec.id}}
        except ValueError as exc:
            return {"error": str(exc)}
        except Exception as exc:  # noqa: BLE001
            return {"error": exc.__class__.__name__}

    def step(self, user_text):
        """Una pasada del loop: pide JSON de acción al modelo; ejecuta 1 tool."""
        from . import chatgpt_oauth as cgo
        tokens = cgo.get_valid_tokens()
        if not tokens:
            return {"done": False, "reply": None, "error": "no_conectado"}
        if tokens.get("needs_reconnect"):
            return {"done": False, "reply": None, "error": "token_vencido_reconectar"}
        import requests
        spec = json.dumps(self.tool_spec(), ensure_ascii=False)
        modelos = ", ".join(self.agente.modelos_ids.mapped("model"))
        prompt = (
            f"Sos el agente '{self.agente.name}'. Herramientas: {spec}. "
            f"Modelos autorizados: {modelos}. "
            "Respondé SOLO JSON: {\"tool\": \"search_read|create\", \"args\": {...}} "
            "o {\"reply\": \"respuesta final\"}. Pregunta: " + user_text[:400]
        )
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        if tokens.get("account_id"):
            headers["ChatGPT-Account-Id"] = tokens["account_id"]
        body = {
            "model": "gpt-6-luna",
            "input": [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}],
            "max_output_tokens": 500,
            "stream": False,
            "store": False,
        }
        try:
            resp = requests.post(cgo.CODEX_API_ENDPOINT, json=body,
                                 headers=headers, timeout=(15, 120))
        except requests.RequestException:
            return {"done": False, "reply": None, "error": "http_request_exception"}
        if resp.status_code not in (200, 201):
            return {"done": False, "reply": None, "error": f"http_{resp.status_code}"}
        try:
            data = resp.json()
        except ValueError:
            return {"done": False, "reply": None, "error": "json_invalido"}
        parts = []
        for item in data.get("output") or []:
            if item.get("type") == "message":
                for part in item.get("content") or []:
                    if part.get("type") == "output_text":
                        parts.append(part.get("text", ""))
        text = "\n".join(parts)
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


def loop_run(env, agente, user_text, max_iter=MAX_ITER):
    loop = AgenteLoop(env, agente)
    for _ in range(max_iter):
        step = loop.step(user_text)
        if step.get("error"):
            return step
        if step.get("done"):
            return step
    return {"done": True, "reply": None, "error": "max_iteraciones"}
