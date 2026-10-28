from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSuscripcion(TransactionCase):

    def setUp(self):
        super().setUp()
        self.plan = self.env["dolan.suscripcion.plan"].create({
            "name": "Plan mensual", "precio": 100.0, "ciclo_dias": 30,
        })
        self.partner = self.env["res.partner"].create({"name": "Cliente sub"})
        hoy = date.today()
        self.sub = self.env["dolan.suscripcion.suscripcion"].create({
            "name": "SUB-1", "partner_id": self.partner.id, "plan_id": self.plan.id,
            "fecha_inicio": hoy - timedelta(days=90), "fecha_ultima": hoy - timedelta(days=61),
        })

    def test_proxima(self):
        self.assertEqual(self.sub.proxima, self.sub.fecha_ultima + timedelta(days=30))

    def test_facturar_vencida_avanza_periodo(self):
        inicial = self.sub.fecha_ultima
        creadas = self.env["dolan.suscripcion.suscripcion"].facturar_programadas()
        self.assertGreaterEqual(creadas, 2)  # 61 dias atras = al menos2 periodos
        self.assertGreater(self.sub.fecha_ultima, inicial)
        moves = self.env["account.move"].search([("ref", "like", "SUB-1")])
        self.assertEqual(len(moves), creadas)
        self.assertTrue(all(m.state == "draft" for m in moves))

    def test_pausada_no_factura(self):
        self.sub.state = "pausada"
        self.assertEqual(self.env["dolan.suscripcion.suscripcion"].facturar_programadas(), 0)
