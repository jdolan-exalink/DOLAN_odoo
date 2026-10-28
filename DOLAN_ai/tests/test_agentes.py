import json
from unittest import mock

from odoo.tests import TransactionCase, tagged

from ..models import agentes as ag


@tagged("post_install", "-at_install")
class TestAgentes(TransactionCase):

    def setUp(self):
        super().setUp()
        partner_model = self.env["ir.model"].search([("model", "=", "res.partner")], limit=1)
        product_model = self.env["ir.model"].search([("model", "=", "product.product")], limit=1)
        self.ag = self.env["dolan.ai.agente"].create({
            "name": "Asistente de contacto",
            "proposito": "buscar contactos",
            "modelos_ids": [(6, 0, [partner_model.id, product_model.id])],
        })

    def test_search_read_autorizado(self):
        loop = ag.AgenteLoop(self.env, self.ag)
        res = loop.run_tool("search_read", {"model": "res.partner", "domain": [], "fields": ["name"], "limit": 2})
        self.assertIn("result", res)

    def test_search_read_modelo_no_autorizado(self):
        loop = ag.AgenteLoop(self.env, self.ag)
        res = loop.run_tool("search_read", {"model": "account.move"})
        self.assertEqual(res.get("error"), "modelo_no_autorizado")

    def test_create_limitado_a_write_models(self):
        loop = ag.AgenteLoop(self.env, self.ag)
        res = loop.run_tool("create", {"model": "product.product", "vals": {"name": "x"}})
        self.assertEqual(res.get("error"), "escritura_no_permitida_en_este_modelo")
        res2 = loop.run_tool("create", {"model": "res.partner", "vals": {"name": "Agente probe"}})
        self.assertIn("id", res2.get("result", {}))
        self.env["res.partner"].browse(res2["result"]["id"]).unlink()

    def test_herramienta_desconocida(self):
        loop = ag.AgenteLoop(self.env, self.ag)
        self.assertEqual(loop.run_tool("unlink", {"model": "res.partner"})["error"], "herramienta_no_autorizada")

    def test_limit_y_dominio(self):
        loop = ag.AgenteLoop(self.env, self.ag)
        res = loop.run_tool("search_read", {"model": "res.partner", "domain": [], "fields": ["name"], "limit": 999})
        self.assertLessEqual(len(res["result"]), ag.MAX_LIMIT)
        res2 = loop.run_tool("search_read", {"model": "res.partner", "domain": "no-lista", "fields": []})
        self.assertEqual(res2.get("error"), "dominio_invalido")

    def test_loop_reply_directo(self):
        reply = json.dumps({"reply": "listo"})
        with mock.patch.object(ag.AgenteLoop, "step") as step:
            step.return_value = {"done": True, "reply": "listo", "tool": None}
            res = ag.loop_run(self.env, self.ag, "hola")
        self.assertTrue(res["done"])
        self.assertEqual(res["reply"], "listo")

    def test_loop_max_iter(self):
        with mock.patch.object(ag.AgenteLoop, "step") as step:
            step.return_value = {"done": False, "tool_result": {"result": []}, "reply": None}
            res = ag.loop_run(self.env, self.ag, "hola", max_iter=3)
        self.assertEqual(res.get("error"), "max_iteraciones")

    def test_step_body_stream_true(self):
        import odoo.addons.DOLAN_ai.models.agentes as ag_mod
        body_captured = {}
        class FakeResp:
            status_code = 200
            def iter_lines(self):
                sse = ('data: ' + json.dumps({"type": "response.output_text.done",
                                              "text": json.dumps({"reply": "hola!"})}) + "\n\n").encode()
                yield sse
        with mock.patch("odoo.addons.DOLAN_ai.models.chatgpt_oauth.get_valid_tokens") as gt, \
             mock.patch("requests.post", return_value=FakeResp()) as post:
            gt.return_value = {"access_token": "t", "refresh_token": "r",
                               "expires_at": 9_999_999_999_999, "account_id": "acc"}
            loop = ag.AgenteLoop(self.env, self.ag)
            res = loop.step("hola")
        self.assertTrue(res["done"])
        self.assertEqual(res["reply"], "hola!")
        b = post.call_args.kwargs.get("json") or {}
        self.assertTrue(b.get("stream"))
        self.assertFalse(b.get("store"))
