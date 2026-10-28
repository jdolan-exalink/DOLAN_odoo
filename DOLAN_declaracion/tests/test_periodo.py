from datetime import date

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPeriodoFiscal(TransactionCase):

    def setUp(self):
        super().setUp()
        self.p = self.env["dolan.fiscal.periodo"].create({
            "name": "Octubre 2026",
            "fecha_desde": date(2026, 10, 1),
            "fecha_hasta": date(2026, 10, 31),
        })

    def test_checklist_se_crea(self):
        self.assertGreaterEqual(len(self.p.item_ids), 6)
        claves = set(self.p.item_ids.mapped("clave"))
        self.assertIn("iva_ventas", claves)
        self.assertIn("cae_pendientes", claves)

    def test_cerrar_bloquea_con_pendientes(self):
        with self.assertRaises(UserError):
            self.p.action_cerrar()
        self.p.item_ids.write({"done": True})
        self.p.action_cerrar()
        self.assertEqual(self.p.state, "cerrado")
        self.p.action_reabrir()
        self.assertEqual(self.p.state, "abierto")

    def test_progreso(self):
        self.p.item_ids[0].done = True
        total = len(self.p.item_ids)
        self.assertEqual(self.p.progreso, round(100 / total))

    def test_datos_iva_shape(self):
        d = self.p.datos_iva()
        self.assertIn("debito", d)
        self.assertIn("credito", d)
        self.assertEqual(d["saldo"], round(d["debito"] - d["credito"], 2))

    def test_cae_pendientes_int(self):
        self.assertIsInstance(self.p.cae_pendientes(), int)
