from datetime import date

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAlquiler(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Cliente alquiler"})
        self.product = self.env["product.product"].create({"name": "Andamio", "type": "service"})
        self.c = self.env["dolan.alquiler.contrato"].create({
            "name": "ALQ-1", "partner_id": self.partner.id, "product_id": self.product.id,
            "fecha_inicio": date(2026, 10, 1), "fecha_fin": date(2026, 10, 10),
            "tarifa_dia": 50.0,
        })

    def test_importes(self):
        self.assertEqual(self.c.dias, 10)
        self.assertEqual(self.c.total, 500.0)

    def test_fechas_invalidas(self):
        self.c.fecha_fin = date(2026, 9, 1)
        self.assertEqual(self.c.dias, 0)
        with self.assertRaises(UserError):
            self.c.action_iniciar()

    def test_facturar(self):
        self.c.action_iniciar()
        self.assertEqual(self.c.state, "activo")
        act = self.c.action_facturar()
        self.assertEqual(act["res_model"], "account.move")
        move = self.env["account.move"].browse(act["res_id"])
        self.assertEqual(move.move_type, "out_invoice")
        self.assertEqual(move.state, "draft")
        self.assertEqual(move.invoice_line_ids.quantity, 10)
        self.assertEqual(move.invoice_line_ids.price_unit, 50.0)
        with self.assertRaises(UserError):
            self.c.action_facturar()
