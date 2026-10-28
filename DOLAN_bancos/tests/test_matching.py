import datetime

from odoo.tests import TransactionCase, tagged

from ..models import matching


@tagged("post_install", "-at_install")
class TestBancosMatching(TransactionCase):

    def _prep(self):
        """Sociedad con diario bancario (My Company no es AR => postea sin CAE)."""
        j = self.env["account.journal"].search([("type", "=", "bank"), ("company_id", "=", 5)], limit=1)
        self.assertTrue(j, "requiere diario bancario en company 1")
        ar = self.env["account.account"].search([("company_ids", "in", [5]), ("account_type", "=", "asset_receivable")], limit=1)
        inc = self.env["account.account"].search([("company_ids", "in", [5]), ("account_type", "=", "income_other")], limit=1)
        if not inc:
            inc = self.env["account.account"].search([("company_ids", "in", [5]), ("account_type", "like", "income")], limit=1)
        self.assertTrue(ar and inc)
        self.p = self.env["res.partner"].create({"name": "Bancos test", "company_id": False})
        # asiento genérico posteado con deudor abierto (equivale a factura impaga)
        move = self.env["account.move"].with_context(allowed_company_ids=[5]).create({
            "move_type": "entry",
            "date": "2026-10-20",
            "line_ids": [
                (0, 0, {"name": "deuda", "account_id": ar.id, "partner_id": self.p.id, "debit": 300.0, "credit": 0.0}),
                (0, 0, {"name": "ingreso", "account_id": inc.id, "debit": 0.0, "credit": 300.0}),
            ],
        })
        move.action_post()
        self.aml_inv = move.line_ids.filtered(lambda l: l.account_id == ar and l.debit)
        self.assertEqual(self.aml_inv.amount_residual, 300.0)
        # statement + line que matchea
        self.line = self.env["account.bank.statement.line"].with_context(allowed_company_ids=[5]).create({
            "journal_id": j.id, "amount": 300.0, "date": "2026-10-26",
            "payment_ref": "TRANSFERENCIA Bancos test", "partner_id": self.p.id,
        })
        self.assertEqual(self.journal(), j)
        return j

    def journal(self):
        return self.line.journal_id

    def test_concilia_exacto(self):
        # importe ÚNICO (487.33) => sin ambigüedad con otros datos de la BD
        self._prep()
        ar = self.aml_inv.account_id
        inc = self.env["account.account"].search([("company_ids", "in", [5]), ("account_type", "like", "income")], limit=1)
        move = self.env["account.move"].with_context(allowed_company_ids=[5]).create({
            "move_type": "entry", "date": "2026-10-20",
            "line_ids": [
                (0, 0, {"name": "deuda 487", "account_id": ar.id, "partner_id": self.p.id, "debit": 487.33, "credit": 0.0}),
                (0, 0, {"name": "ingreso", "account_id": inc.id, "debit": 0.0, "credit": 487.33}),
            ],
        })
        move.action_post()
        self.aml_inv = move.line_ids.filtered(lambda l: l.account_id.account_type == "asset_receivable")
        self.line = self.env["account.bank.statement.line"].with_context(allowed_company_ids=[5]).create({
            "journal_id": self.line.journal_id.id, "amount": 487.33, "date": "2026-10-26",
            "payment_ref": "DBG-EXACTO-1", "partner_id": self.p.id,
        })
        matching.conciliar(self.env)
        self.assertTrue(self.aml_inv.reconciled)
        self.assertTrue(self.line.is_reconciled)
        aml = self.env["account.move.line"].browse(self.aml_inv.id)
        self.assertTrue(aml.reconciled)

    def test_ambiguo_no_concilia(self):
        self._prep()
        ar = self.aml_inv.account_id
        inc = self.env["account.account"].search([("company_ids", "in", [5]), ("account_type", "like", "income")], limit=1)
        move2 = self.env["account.move"].with_context(allowed_company_ids=[5]).create({
            "move_type": "entry", "date": "2026-10-21",
            "line_ids": [
                (0, 0, {"name": "deuda2", "account_id": ar.id, "partner_id": self.p.id, "debit": 300.0, "credit": 0.0}),
                (0, 0, {"name": "ingreso2", "account_id": inc.id, "debit": 0.0, "credit": 300.0}),
            ],
        })
        move2.action_post()
        res = matching.conciliar(self.env)
        self.assertGreaterEqual(res["ambiguas"], 1)
        self.assertFalse(self.line.is_reconciled)

    def test_import_csv(self):
        self._prep()
        csv_text = ("fecha,referencia,debito,credito,partner\n"
                    "2026-10-27,COBRO_CLIENTE,0,300.00,Bancos test\n")
        res = matching.importar_extracto(self.env, csv_text, journal_id=self.line.journal_id.id)
        self.assertTrue(res["ok"])
        self.assertEqual(res["lineas"], 1)
        st_line = self.env["account.bank.statement.line"].search([("payment_ref", "=", "COBRO_CLIENTE")], limit=1)
        self.assertTrue(st_line)
        self.assertEqual(st_line.amount, 300.0)
