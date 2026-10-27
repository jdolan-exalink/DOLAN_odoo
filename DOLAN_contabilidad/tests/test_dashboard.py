from odoo.tests import TransactionCase, tagged

from ..models.dashboard import kpis


@tagged("post_install", "-at_install")
class TestContabilidadKpi(TransactionCase):

    def test_kpis_shape(self):
        d = kpis(self.env)
        for key in ("emitidas", "recibidas", "monto_emitido", "iva_debito", "iva_credito", "iva_liquidado"):
            self.assertIn(key, d)
            self.assertIsInstance(d[key], (int, float))

    def test_iva_con_datos_reales(self):
        aml = self.env["account.move.line"].search([
            ("tax_line_id", "!=", False), ("move_id.state", "=", "posted"),
        ], limit=1, order="date desc")
        if not aml:
            self.skipTest("sin lineas de impuesto publicadas en la BD")
        d = kpis(self.env, hoy=aml.date)
        self.assertGreaterEqual(d["iva_debito"] + d["iva_credito"], 0)
        self.assertEqual(
            d["iva_liquidado"], round(d["iva_debito"] - d["iva_credito"], 2))
