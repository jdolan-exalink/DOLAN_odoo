from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaller(TransactionCase):

    def setUp(self):
        super().setUp()
        self.wc = self.env["mrp.workcenter"].create({"name": "Banco 1", "costs_hour": 10.0})
        self.t = self.env["dolan.taller.turno"].create({
            "name": "T-1", "workcenter_id": self.wc.id,
        })

    def test_minutos_corriendo(self):
        self.assertGreaterEqual(self.t.minutos, 0.0)

    def test_pausar_reanudar_terminar(self):
        self.t.action_pausar()
        self.assertEqual(self.t.state, "pausado")
        self.assertTrue(self.t.fin)
        self.t.action_reanudar()
        self.assertEqual(self.t.state, "corriendo")
        self.assertFalse(self.t.fin)
        self.t.action_terminar()
        self.assertEqual(self.t.state, "terminado")
        with self.assertRaises(UserError):
            self.t.action_pausar()

    def test_consumo(self):
        prod = self.env["product.product"].create({"name": "Tornillos", "type": "consu", "is_storable": True})
        self.env["dolan.taller.consumo"].create({
            "turno_id": self.t.id, "product_id": prod.id, "cantidad": 24,
        })
        self.assertEqual(len(self.t.consumo_ids), 1)

    def test_qc_liga_calidad(self):
        punto = self.env["dolan.calidad.punto_control"].create({"name": "Control banco", "ambito": "operacion"})
        ctrl = self.t.qc_crear(punto.id)
        self.assertEqual(ctrl.taller_turno_id.id, self.t.id)
        self.assertEqual(ctrl.punto_id.id, punto.id)
