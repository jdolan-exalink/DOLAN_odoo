import json
from unittest import mock

from odoo.tests import TransactionCase, tagged

from ..models import ocr


def _fake_resp(status, payload):
    r = mock.Mock()
    r.status_code = status
    r.json.return_value = payload
    r.text = json.dumps(payload)
    return r


DATOS = {
    "proveedor": "Proveedor OCR SA",
    "cuit": "30-12345678-9",
    "fecha": "2026-10-20",
    "tipo_doc": "Factura B",
    "numero": "0001-00001234",
    "total": 1210.0,
    "lineas": [{"descripcion": "Cemento", "cantidad": 10, "precio": 100.0}],
}


@tagged("post_install", "-at_install")
class TestOcr(TransactionCase):

    def test_parse_json_con_fences(self):
        self.assertEqual(ocr.parse_ocr_text('```json\n{"total": 5}\n```'), {"total": 5})
        self.assertIsNone(ocr.parse_ocr_text("sin json"))
        self.assertIsNone(ocr.parse_ocr_text(""))
        self.assertIsNone(ocr.parse_ocr_text('{"no_dict": [1]}'))

    def test_extract_usa_token_y_parsea(self):
        body_captured = {}
        def fake_post(url, **kw):
            body_captured.update(kw.get("json") or {})
            r = mock.Mock()
            r.status_code = 200
            sse = ('data: ' + json.dumps({"type": "response.output_text.done",
                                          "text": json.dumps(DATOS)}) + "\n\n").encode()
            r.iter_lines.return_value = [sse]
            return r
        with mock.patch("odoo.addons.DOLAN_ai.models.chatgpt_oauth.get_valid_tokens") as gt, \
             mock.patch("requests.post", side_effect=fake_post):
            gt.return_value = {"access_token": "t", "refresh_token": "r",
                               "expires_at": 9_999_999_999_999, "account_id": "acc"}
            res = ocr.extract_from_image(self.env, "data:image/png;base64,AAAA")
        self.assertTrue(res["ok"])
        self.assertEqual(res["datos"]["proveedor"], "Proveedor OCR SA")
        self.assertEqual(body_captured["input"][0]["content"][1]["type"], "input_image")
        self.assertTrue(body_captured["stream"])

    def test_map_sin_lineas_usa_total(self):
        d = {"proveedor": "P", "total": 500.0, "lineas": []}
        m = ocr.map_to_draft(self.env, d)
        self.assertTrue(m["ok"])
        self.assertEqual(m["vals"]["lineas"][0]["price_unit"], 500.0)

    def test_map_vacio_rechaza(self):
        m = ocr.map_to_draft(self.env, {"proveedor": "P"})
        self.assertFalse(m["ok"])
        self.assertEqual(m["error"], "sin_lineas_ni_total")

    def test_create_draft_end_to_end(self):
        res = ocr.create_draft(self.env, DATOS)
        self.assertTrue(res["ok"], res)
        move = self.env["account.move"].browse(res["move_id"])
        self.assertEqual(move.move_type, "in_invoice")
        self.assertEqual(move.state, "draft")
        self.assertIn("Proveedor OCR SA", move.partner_id.name)
        line = move.invoice_line_ids[0]
        self.assertEqual(line.quantity, 10)
        self.assertEqual(line.price_unit, 100.0)
        # limpieza
        move.unlink()
        partner = self.env["res.partner"].search([("name", "=", "Proveedor OCR SA")])
        partner.unlink()

    def test_build_body_shape(self):
        b = ocr.build_ocr_body("data:image/jpeg;base64,XYZ")
        self.assertEqual(b["model"], "gpt-6-luna")
        parts = b["input"][0]["content"]
        self.assertEqual(parts[0]["type"], "input_text")
        self.assertEqual(parts[1]["type"], "input_image")
        self.assertFalse(b["store"])


@tagged("post_install", "-at_install")
class TestOcrPdf(TransactionCase):

    def test_pdf_imagen_rasteriza(self):
        import io
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (400, 300), "white")
        ImageDraw.Draw(img).text((20, 20), "TOTAL: 1210.00", fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PDF")
        pages = ocr.pdf_to_images(buf.getvalue())
        self.assertTrue(pages)
        self.assertTrue(pages[0].startswith("data:image/png;base64,"))

    def test_build_text_body(self):
        b = ocr.build_ocr_text_body("CUIT 30-... TOTAL 1210")
        self.assertTrue(b["stream"])
        self.assertIn("input_text", b["input"][0]["content"][0]["type"])


@tagged("post_install", "-at_install")
class TestOcrFechas(TransactionCase):

    def test_norm_date(self):
        self.assertEqual(ocr._norm_date("2026-10-25"), "2026-10-25")
        self.assertEqual(ocr._norm_date("25/10/2026"), "2026-10-25")
        self.assertEqual(ocr._norm_date("25-10-2026"), "2026-10-25")
        self.assertFalse(ocr._norm_date(""))
        self.assertFalse(ocr._norm_date("ayer"))
        self.assertFalse(ocr._norm_date(None))

    def test_map_fecha_ddmm(self):
        d = {"proveedor": "P", "total": 100.0, "fecha": "05/03/2026", "lineas": []}
        m = ocr.map_to_draft(self.env, d)
        self.assertEqual(m["vals"]["invoice_date"], "2026-03-05")

    def test_create_usuario_normal(self):
        # como juan (no superuser) — garantiza que create_draft no dependa del shell root
        res = ocr.create_draft(self.env, {
            "proveedor": "OCR USER SA", "fecha": "05/03/2026", "numero": "0004-00000001",
            "total": 121.0, "lineas": [{"descripcion": "Item", "cantidad": 1, "precio": 100.0}],
        })
        self.assertTrue(res["ok"], res)
        move = self.env["account.move"].browse(res["move_id"])
        self.assertEqual(move.state, "draft")
        move.unlink()
        self.env["res.partner"].search([("name", "=", "OCR USER SA")]).unlink()


@tagged("post_install", "-at_install")
class TestOcrMultiCompany(TransactionCase):

    def test_partner_otra_compania(self):
        # compañía distinta con diario de compras (migración multi-compañía real)
        j = self.env["account.journal"].search([
            ("type", "=", "purchase"), ("company_id", "!=", self.env.company.id)], limit=1)
        self.assertTrue(j, "requiere otra compañía con diario de compras")
        comp2 = j.company_id
        p2 = self.env["res.partner"].create({"name": "Proveedor otra comp", "company_id": comp2.id})
        res = ocr.create_draft(self.env, {
            "proveedor": "Proveedor otra comp", "fecha": "2026-10-26", "total": 121.0,
            "lineas": [{"descripcion": "Item", "cantidad": 1, "precio": 100.0}],
        })
        self.assertTrue(res["ok"], res)
        move = self.env["account.move"].browse(res["move_id"])
        self.assertEqual(move.company_id.id, comp2.id)
        self.assertEqual(move.partner_id.id, p2.id)
        move.unlink()
        p2.unlink()

    def test_partner_nuevo_compartido(self):
        res = ocr.create_draft(self.env, {
            "proveedor": "Proveedor compartido OCR", "total": 50.0,
            "lineas": [{"descripcion": "x", "cantidad": 1, "precio": 50.0}],
        })
        self.assertTrue(res["ok"], res)
        move = self.env["account.move"].browse(res["move_id"])
        self.assertFalse(move.partner_id.company_id)
        move.unlink()
        self.env["res.partner"].search([("name", "=", "Proveedor compartido OCR")]).unlink()
