from datetime import timedelta

from odoo.addons.report_xlsx.report.report_abstract_xlsx import ReportXlsxAbstract

from odoo.addons.DOLAN_contabilidad.models.financial_report import (
    ACTIVO_CORRIENTE,
    ACTIVO_NO_CORRIENTE,
    COSTOS,
    GASTOS,
    INGRESOS,
    PASIVO_CORRIENTE,
    PASIVO_NO_CORRIENTE,
    PATRIMONIO,
)


class DolanFinancialReportXlsx(ReportXlsxAbstract):
    """Estados financieros DOLAN en XLSX (LGPL): balance general, estado de
    resultados y flujo de efectivo. Cálculo propio sobre account.move.line por
    tipo de cuenta; sin dependencias de módulos externos de reportes."""

    _name = "report.dolan_contabilidad.financial_report"
    _description = "Estados financieros DOLAN (XLSX)"

    # -- helpers -------------------------------------------------------
    def _money(self, workbook):
        return workbook.add_format({"num_format": "#,##0.00;[Red]-#,##0.00"})

    def _formats(self, workbook):
        return {
            "title": workbook.add_format({"bold": True, "font_size": 14}),
            "sub": workbook.add_format({"italic": True, "font_size": 10, "font_color": "#555555"}),
            "section": workbook.add_format({"bold": True, "bg_color": "#EEF2FF", "border": 1}),
            "label": workbook.add_format({"indent": 1}),
            "money": self._money(workbook),
            "total_label": workbook.add_format({"bold": True, "top": 1}),
            "total_money": workbook.add_format({"bold": True, "top": 1, "num_format": "#,##0.00;[Red]-#,##0.00"}),
            "warn": workbook.add_format({"bold": True, "font_color": "#B45309"}),
        }

    def _row(self, sheet, row, label, value, f, money_bold=False):
        sheet.write(row, 0, label, f["total_label"] if money_bold else f["label"])
        sheet.write_number(row, 1, round(value or 0.0, 2),
                           f["total_money"] if money_bold else f["money"])
        return row + 1

    def _section(self, sheet, row, title, f):
        sheet.write(row, 0, title, f["section"])
        sheet.write(row, 1, "", f["section"])
        return row + 1

    def _header(self, sheet, wiz, f, titulo):
        sheet.set_column(0, 0, 46)
        sheet.set_column(1, 1, 20)
        sheet.write(0, 0, f"{wiz.env.company.name} — {titulo}", f["title"])
        periodo = f"Período: {wiz.date_from.strftime('%d/%m/%Y')} al {wiz.date_to.strftime('%d/%m/%Y')}"
        sheet.write(1, 0, periodo, f["sub"])
        return 3

    # -- reporte -------------------------------------------------------
    def generate_xlsx_report(self, workbook, data, objs):
        wiz = objs[0]
        f = self._formats(workbook)
        nombres = {"balance": "Balance", "results": "Resultados", "cash": "Flujo"}
        sheet = workbook.add_worksheet(nombres.get(wiz.report_type, "Reporte"))
        if wiz.report_type == "balance":
            self._balance(sheet, wiz, f)
        elif wiz.report_type == "results":
            self._results(sheet, wiz, f)
        else:
            self._cash(sheet, wiz, f)

    def _balance(self, sheet, wiz, f):
        row = self._header(sheet, wiz, f, "Balance general")
        # los activos/pasivos/patrimonio se acumulan desde el inicio
        tot = wiz._sums_by_type(date_to=wiz.date_to)

        row = self._section(sheet, row, "ACTIVO", f)
        corriente = wiz._group(tot, ACTIVO_CORRIENTE)
        no_corriente = wiz._group(tot, ACTIVO_NO_CORRIENTE)
        row = self._row(sheet, row, "Activo corriente", corriente, f)
        row = self._row(sheet, row, "Activo no corriente", no_corriente, f)
        row = self._row(sheet, row, "TOTAL ACTIVO", corriente + no_corriente, f, money_bold=True)
        total_activo = corriente + no_corriente
        row += 1

        row = self._section(sheet, row, "PASIVO", f)
        # en Odoo el crédito es saldo negativo: se presentan en positivo
        pc = -wiz._group(tot, PASIVO_CORRIENTE)
        pnc = -wiz._group(tot, PASIVO_NO_CORRIENTE)
        row = self._row(sheet, row, "Pasivo corriente", pc, f)
        row = self._row(sheet, row, "Pasivo no corriente", pnc, f)
        row = self._row(sheet, row, "TOTAL PASIVO", pc + pnc, f, money_bold=True)
        total_pasivo = pc + pnc
        row += 1

        row = self._section(sheet, row, "PATRIMONIO", f)
        neto = -wiz._group(tot, PATRIMONIO)
        resultado = -(wiz._group(tot, INGRESOS + COSTOS + GASTOS))
        row = self._row(sheet, row, "Patrimonio neto", neto, f)
        row = self._row(sheet, row, "Resultado del ejercicio", resultado, f)
        row = self._row(sheet, row, "TOTAL PATRIMONIO", neto + resultado, f, money_bold=True)
        row += 1

        descuadre = total_activo - (total_pasivo + neto + resultado)
        sheet.write(row, 0, "Control (Activo − Pasivo − Patrimonio)", f["total_label"])
        sheet.write_number(row, 1, round(descuadre, 2),
                           f["total_money"] if abs(descuadre) < 0.01 else f["warn"])

    def _results(self, sheet, wiz, f):
        row = self._header(sheet, wiz, f, "Estado de resultados")
        tot = wiz._sums_by_type(date_from=wiz.date_from, date_to=wiz.date_to)

        row = self._section(sheet, row, "INGRESOS", f)
        ventas = -wiz._group(tot, ["income"])
        otros = -wiz._group(tot, ["income_other"])
        row = self._row(sheet, row, "Ventas e ingresos operativos", ventas, f)
        row = self._row(sheet, row, "Otros ingresos", otros, f)
        row = self._row(sheet, row, "TOTAL INGRESOS", ventas + otros, f, money_bold=True)
        row += 1

        row = self._section(sheet, row, "GASTOS", f)
        costo = wiz._group(tot, COSTOS)
        gastos = wiz._group(tot, GASTOS)
        row = self._row(sheet, row, "Costo de ventas", costo, f)
        row = self._row(sheet, row, "Gastos de explotación, deprec. y otros", gastos, f)
        row = self._row(sheet, row, "TOTAL GASTOS", costo + gastos, f, money_bold=True)
        row += 1

        self._row(sheet, row, "RESULTADO DEL EJERCICIO", (ventas + otros) - (costo + gastos), f, money_bold=True)

    def _cash(self, sheet, wiz, f):
        row = self._header(sheet, wiz, f, "Flujo de efectivo (bancos y caja)")
        tipos = ["asset_cash"]
        inicial = wiz._sum(tipos, date_to=wiz.date_from - timedelta(days=1))
        final = wiz._group(wiz._sums_by_type(date_to=wiz.date_to), tipos)
        variacion = wiz._group(wiz._sums_by_type(date_from=wiz.date_from, date_to=wiz.date_to), tipos)

        row = self._section(sheet, row, "EFECTIVO", f)
        row = self._row(sheet, row, "Saldo inicial de bancos y caja", inicial, f)
        row = self._row(sheet, row, "Variación neta del período", variacion, f)
        row = self._row(sheet, row, "SALDO FINAL", final, f, money_bold=True)
        row += 1

        row = self._section(sheet, row, "POR DIARIO", f)
        journals = self.env["account.journal"].search(
            [("company_id", "=", wiz.env.company.id), ("type", "in", ("bank", "cash"))])
        for journal in journals:
            saldo = sum(
                line.balance or 0.0
                for line in self.env["account.move.line"].search([
                    ("company_id", "=", wiz.env.company.id),
                    ("parent_state", "=", "posted"),
                    ("journal_id", "=", journal.id),
                    ("account_id.account_type", "in", tipos),
                    ("date", "<=", wiz.date_to),
                ]))
            row = self._row(sheet, row, f"{journal.name} ({journal.type})", saldo, f)
