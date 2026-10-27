from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged

from ..models.dashboard import kpis


@tagged("post_install", "-at_install")
class TestMantenimientoKpi(TransactionCase):

    def test_kpis_flujo(self):
        d0 = kpis(self.env)
        self.assertEqual(d0["ot_abiertas"], 0)
        self.assertEqual(d0["equipos"], 0)
        eq = self.env["maintenance.equipment"].create({"name": "Compresor 1"})
        ot = self.env["maintenance.request"].create({
            "name": "Falla probe",
            "equipment_id": eq.id,
            "schedule_date": fields.Date.today(),
        })
        d1 = kpis(self.env)
        self.assertEqual(d1["ot_abiertas"], 1)
        self.assertEqual(d1["equipos"], 1)
        self.assertEqual(d1["ot_atrasadas"], 0)
        ot.schedule_date = fields.Date.today() - timedelta(days=1)
        d2 = kpis(self.env)
        self.assertEqual(d2["ot_atrasadas"], 1)
        self.assertEqual(d2["ot_abiertas"], 1)
