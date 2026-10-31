from odoo.addons.report_xlsx.report.report_abstract_xlsx import ReportXlsxAbstract

from odoo.addons.DOLAN_contabilidad.models.financial_report import (
    ACTIVO_CORRIENTE, ACTIVO_NO_CORRIENTE, COSTOS, GASTOS, INGRESOS,
    PASIVO_CORRIENTE, PASIVO_NO_CORRIENTE, PATRIMONIO,
)


class DolanAnnualReportXlsx(ReportXlsxAbstract):
    _name = "report.dolan_contabilidad.annual_report"
    _description = "Reporte anual DOLAN (XLSX)"

    def _formats(self, workbook):
        return {
            "title": workbook.add_format({"bold": True, "font_size": 14}),
            "sub": workbook.add_format({"italic": True, "font_size": 10, "font_color": "#555555"}),
            "head": workbook.add_format({"bold": True, "bg_color": "#EEF2FF", "border": 1}),
            "label": workbook.add_format(),
            "money": workbook.add_format({"num_format": "#,##0.00;[Red]-#,##0.00"}),
            "total": workbook.add_format({"bold": True, "top": 1, "num_format": "#,##0.00;[Red]-#,##0.00"}),
            "text": workbook.add_format({"border": 1}),
        }

    def generate_xlsx_report(self, workbook, data, objs):
        wiz = objs[0]
        f = self._formats(workbook)
        sheet = workbook.add_worksheet("Anual")
        sheet.set_column(0, 0, 46)
        sheet.set_column(1, 1, 20)
        sheet.write(0, 0, "%s — Reporte anual" % wiz.env.company.name, f["title"])
        sheet.write(1, 0, "Ejercicio: %s al %s" % (
            wiz.date_from.strftime("%d/%m/%Y"), wiz.date_to.strftime("%d/%m/%Y")), f["sub"])

        totals = wiz._sums(date_to=wiz.date_to)
        period = wiz._sums(date_from=wiz.date_from, date_to=wiz.date_to)
        row = 3

        row = self._section(sheet, row, "RESUMEN DE RESULTADOS", f)
        ingresos = -wiz._group(period, INGRESOS)
        gastos = wiz._group(period, COSTOS + GASTOS)
        row = self._row(sheet, row, "Ingresos", ingresos, f)
        row = self._row(sheet, row, "Costos y gastos", gastos, f)
        row = self._row(sheet, row, "Resultado del ejercicio", ingresos - gastos, f, True)
        row += 1

        row = self._section(sheet, row, "BALANCE RESUMIDO (al cierre)", f)
        activo = wiz._group(totals, ACTIVO_CORRIENTE) + wiz._group(totals, ACTIVO_NO_CORRIENTE)
        pasivo = -(wiz._group(totals, PASIVO_CORRIENTE) + wiz._group(totals, PASIVO_NO_CORRIENTE))
        patrimonio = -wiz._group(totals, PATRIMONIO)
        row = self._row(sheet, row, "Activo", activo, f)
        row = self._row(sheet, row, "Pasivo", pasivo, f)
        row = self._row(sheet, row, "Patrimonio neto", patrimonio, f)
        row = self._row(sheet, row, "Resultado del ejercicio (acumulado)",
                        activo - pasivo - patrimonio, f, True)
        row += 1

        row = self._section(sheet, row, "ARCHIVOS DE TRABAJO", f)
        wp = wiz.env["dolan.workpaper"].search([
            ("date_from", ">=", wiz.date_from), ("date_to", "<=", wiz.date_to)])
        for state, label in (("draft", "Borradores"), ("review", "En revision"),
                             ("approved", "Aprobados")):
            rows = wp.filtered(lambda w: w.state == state)
            sheet.write(row, 0, "%s (%d)" % (label, len(rows)), f["label"])
            sheet.write(row, 1, ", ".join(rows.mapped("title"))[:120] or "-", f["text"])
            row += 1
        sheet.write(row, 0, "Total", f["label"])
        sheet.write_number(row, 1, len(wp), f["total"])
        row += 2

        row = self._section(sheet, row, "INDICADORES DEL EJERCICIO", f)
        moves = wiz.env["account.move"].search([
            ("company_id", "=", wiz.env.company.id), ("state", "=", "posted"),
            ("date", ">=", wiz.date_from), ("date", "<=", wiz.date_to)])
        facturas = moves.filtered(lambda m: m.move_type in ("out_invoice", "out_refund"))
        sheet.write(row, 0, "Comprobantes publicados (%d)" % len(moves), f["label"])
        sheet.write_number(row, 1, len(moves), f["money"])
        row += 1
        sheet.write(row, 0, "Facturas de venta y NC (%d)" % len(facturas), f["label"])
        sheet.write_number(row, 1, len(facturas), f["money"])

    def _section(self, sheet, row, title, f):
        sheet.write(row, 0, title, f["head"])
        sheet.write(row, 1, "", f["head"])
        return row + 1

    def _row(self, sheet, row, label, value, f, bold=False):
        sheet.write(row, 0, label, f["label"])
        sheet.write_number(row, 1, round(value or 0.0, 2), f["total"] if bold else f["money"])
        return row + 1
