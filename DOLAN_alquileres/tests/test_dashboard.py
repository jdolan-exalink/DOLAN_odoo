from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged

from ..models.dashboard import kpis


@tagged("post_install", "-at_install")
class TestAlquilerKpis(TransactionCase):

    def setUp(self):
        super().setUp()
        p = self.env["res.partner"].create({"name": "Cliente kpi"})
        prod = self.env["product.product"].create({"name": "Bien kpi", "type": "service"})
        C = self.env["dolan.alquiler.contrato"]
        self.base = kpis(self.env)
        self.hoy = C.create({"name": "K-1", "partner_id": p.id, "product_id": prod.id,
                             "fecha_inicio": date.today(), "fecha_fin": date.today() + timedelta(days=2),
                             "tarifa_dia": 10.0})
        self.vencido = C.create({"name": "K-2", "partner_id": p.id, "product_id": prod.id,
                                 "fecha_inicio": date.today() - timedelta(days=5),
                                 "fecha_fin": date.today() - timedelta(days=1),
                                 "tarifa_dia": 10.0, "estado_ops": "recolectada"})

    def test_kpis_deltas(self):
        d = kpis(self.env)
        self.assertEqual(d["hoy"] - self.base["hoy"], 1)
        self.assertEqual(d["tarde"] - self.base["tarde"], 1)
        self.assertEqual(d["por_confirmar"] - self.base["por_confirmar"], 2)
        self.assertEqual(d["por_facturar"], self.base["por_facturar"])

    def test_por_facturar_y_estado(self):
        self.hoy.state = "activo"
        d = kpis(self.env)
        self.assertEqual(d["por_facturar"] - self.base["por_facturar"], 1)
        self.assertEqual(self.hoy.estado_factura, "sin_factura")
        self.hoy.action_facturar()
        self.assertEqual(self.hoy.estado_factura, "por_facturar")
