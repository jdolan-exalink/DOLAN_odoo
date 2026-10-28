from odoo.tests import TransactionCase, tagged

from ..models.lookup import lookup


@tagged("post_install", "-at_install")
class TestLookupV2(TransactionCase):

    def setUp(self):
        super().setUp()
        self.loc = self.env.ref("stock.stock_location_stock")
        self.p = self.env["product.product"].create({
            "name": "Probe barras", "barcode": "7791234567890",
            "type": "consu", "is_storable": True, "default_code": "SKU-PROBE-1",
        })

    def test_no_encontrado(self):
        self.assertEqual(lookup(self.env, "999")["error"], "no_encontrado")
        self.assertEqual(lookup(self.env, "  ")["error"], "codigo_vacio")

    def test_producto_con_existencias(self):
        self.env["stock.quant"].sudo().create({
            "product_id": self.p.id, "location_id": self.loc.id, "quantity": 7.0,
        })
        r = lookup(self.env, "7791234567890")
        self.assertTrue(r["ok"])
        self.assertEqual(r["tipo"], "producto")
        self.assertEqual(r["total"], 7.0)
        self.assertTrue(lookup(self.env, "SKU-PROBE-1")["ok"])

    def test_picking(self):
        partner = self.env["res.partner"].create({"name": "Prov scan"})
        pick = self.env["stock.picking"].create({
            "picking_type_id": self.env.ref("stock.picking_type_in").id,
            "location_id": self.env.ref("stock.stock_location_suppliers").id,
            "location_dest_id": self.loc.id,
            "partner_id": partner.id,
        })
        pick.name = "TESTPICK-001"
        r = lookup(self.env, "TESTPICK-001")
        self.assertTrue(r["ok"])
        self.assertEqual(r["tipo"], "picking")
        self.assertTrue(r["action_id"])

    def test_contacto_por_ref(self):
        partner = self.env["res.partner"].create({"name": "Cli scan", "ref": "CLI-99"})
        r = lookup(self.env, "CLI-99")
        self.assertTrue(r["ok"])
        self.assertEqual(r["tipo"], "partner")
        self.assertIn(partner.display_name, r["titulo"])

    def test_tipo_operacion(self):
        ptype = self.env["stock.picking.type"].search([], limit=1)
        self.assertTrue(ptype)
        r = lookup(self.env, ptype.code)
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["tipo"], "operacion")
        self.assertEqual(r["code"], ptype.code)
