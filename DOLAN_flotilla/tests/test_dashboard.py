from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged

from ..models.dashboard import kpis


@tagged("post_install", "-at_install")
class TestFlotillaKpi(TransactionCase):

    def test_kpis_contratos(self):
        v = self.env["fleet.vehicle"].create({"name": "Camioneta 1", "model_id": self.env["fleet.vehicle.model"].create({"name": "Modelo X", "brand_id": self.env["fleet.vehicle.model.brand"].create({"name": "Marca X"}).id}).id})
        LC = self.env["fleet.vehicle.log.contract"].create({
            "vehicle_id": v.id,
            "start_date": date.today() - timedelta(days=10),
            "expiration_date": date.today() + timedelta(days=10),
            "amount": 100.0,
        })
        d = kpis(self.env)
        self.assertEqual(d["vehiculos"], 1)
        self.assertEqual(d["contratos_por_vencer_30d"], 1)
        LC.expiration_date = date.today() - timedelta(days=1)
        d2 = kpis(self.env)
        self.assertEqual(d2["contratos_vencidos"], 1)
        self.assertEqual(d2["contratos_por_vencer_30d"], 0)
