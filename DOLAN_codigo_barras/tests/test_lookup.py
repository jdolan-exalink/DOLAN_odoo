from odoo.tests import TransactionCase, tagged

from ..models.lookup import lookup


@tagged("post_install", "-at_install")
class TestLookup(TransactionCase):

    def setUp(self):
        super().setUp()
        self.loc = self.env.ref("stock.stock_location_stock")
        self.p = self.env["product.product"].create({
            "name": "Probe barras",
            "barcode": "7791234567890",
            "type": "consu",
            "is_storable": True,
            "default_code": "SKU-PROBE-1",
        })

    def test_no_encontrado(self):
        r = lookup(self.env, "999")
        self.assertFalse(r["ok"])
        self.assertEqual(r["error"], "no_encontrado")
        self.assertEqual(lookup(self.env, "   ")["error"], "codigo_vacio")

    def test_encontrado_con_existencias(self):
        self.env["stock.quant"].sudo().create({
            "product_id": self.p.id, "location_id": self.loc.id, "quantity": 7.0,
        })
        r = lookup(self.env, "7791234567890")
        self.assertTrue(r["ok"])
        self.assertEqual(r["producto"]["sku"], "SKU-PROBE-1")
        self.assertEqual(r["total"], 7.0)
        # fallback SKU
        r2 = lookup(self.env, "SKU-PROBE-1")
        self.assertTrue(r2["ok"])
