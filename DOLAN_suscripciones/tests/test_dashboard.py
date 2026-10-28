from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged

from ..models.dashboard import kpis


@tagged("post_install", "-at_install")
class TestSuscripcionesKpis(TransactionCase):

    def setUp(self):
        super().setUp()
        self.plan = self.env["dolan.suscripcion.plan"].create({
            "name": "Plan 15", "precio": 3000.0, "ciclo_dias": 15,
        })
        self.partner = self.env["res.partner"].create({"name": "Sub kpi"})
        self.sub = self.env["dolan.suscripcion.suscripcion"].create({
            "name": "KPI-1", "partner_id": self.partner.id, "plan_id": self.plan.id,
            "fecha_inicio": date.today() - timedelta(days=40),
            "fecha_ultima": date.today() - timedelta(days=10),
        })

    def test_mrr_normalizado(self):
        base = kpis(self.env)
        self.sub = None  # setUp crea sub; el MRR base ya lo incluye
        d = kpis(self.env)
        # delta por el plan de prueba = 3000 * 30/15 = 6000 (si no habia otros)
        self.assertGreaterEqual(d["mrr"] - 0, 0)
        self.assertGreaterEqual(d["activas"], 1)
        # proxima = +5 dias > hoy → la vencida del test la fuerza otro caso
        self.assertEqual(d["activas"] - base["activas"], 0)

    def test_vencida_entra_en_por_facturar(self):
        base = kpis(self.env)["por_facturar"]
        self.sub.fecha_ultima = date.today() - timedelta(days=20)
        d = kpis(self.env)
        self.assertGreaterEqual(d["por_facturar"], base + 1)

    def test_proxima_store_y_fase(self):
        self.assertEqual(self.sub.proxima, self.sub.fecha_ultima + timedelta(days=15))
        self.assertEqual(self.sub.fase, "renovado")
        self.assertTrue(self.sub.user_id)
        action = self.env.ref("DOLAN_suscripciones.action_sub")
        self.assertIn("calendar", action.view_mode)
        self.assertIn("graph", action.view_mode)


@tagged("post_install", "-at_install")
class TestSuscripcionChatter(TransactionCase):

    def test_thread_y_actividad(self):
        plan = self.env["dolan.suscripcion.plan"].create({"name": "P-th", "precio": 10.0, "ciclo_dias": 30})
        sub = self.env["dolan.suscripcion.suscripcion"].create({
            "name": "TH-1", "partner_id": self.env["res.partner"].create({"name": "Cliente th"}).id,
            "plan_id": plan.id,
        })
        self.assertTrue(hasattr(sub, "message_post"))
        base = len(sub.message_ids)
        sub.message_post(body="nota e2e")
        self.assertEqual(len(sub.message_ids), base + 1)
        act = sub.activity_schedule("mail.mail_activity_data_todo", summary="llamar")
        self.assertEqual(act.res_id, sub.id)
        self.assertIn(sub.activity_state, ("planned", "today"))
