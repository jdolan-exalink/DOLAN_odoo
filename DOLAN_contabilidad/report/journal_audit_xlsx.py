import re

from odoo.addons.report_xlsx.report.report_abstract_xlsx import ReportXlsxAbstract


class DolanJournalAuditXlsx(ReportXlsxAbstract):
    """Auditoría de diario DOLAN (XLSX, LGPL). Modelo de referencia: el reporte
    "Auditoría de diario" de Enterprise (columnas Documentos | Por revisar |
    Deber | Haber | Balance) + controles propios de secuencia y borradores."""

    _name = "report.dolan_contabilidad.journal_audit"
    _description = "Auditoría de diario DOLAN (XLSX)"

    def _formats(self, workbook):
        money = workbook.add_format({"num_format": "#,##0.00;[Red]-#,##0.00"})
        return {
            "title": workbook.add_format({"bold": True, "font_size": 14}),
            "sub": workbook.add_format({"italic": True, "font_size": 10, "font_color": "#555555"}),
            "head": workbook.add_format({"bold": True, "bg_color": "#EEF2FF", "border": 1}),
            "cell": workbook.add_format({"border": 1}),
            "money": money,
            "money_bold": workbook.add_format({"bold": True, "top": 1, "num_format": "#,##0.00;[Red]-#,##0.00"}),
            "label_bold": workbook.add_format({"bold": True, "top": 1}),
            "alert": workbook.add_format({"font_color": "#B45309", "bold": True}),
        }

    def _header(self, sheet, wiz, f, titulo):
        sheet.set_column(0, 0, 26)
        sheet.set_column(1, 1, 14)
        sheet.set_column(2, 4, 14)
        sheet.set_column(5, 6, 16)
        sheet.write(0, 0, f"{wiz.company_id.name} — {titulo}", f["title"])
        sheet.write(1, 0, f"Período: {wiz.date_from.strftime('%d/%m/%Y')} al {wiz.date_to.strftime('%d/%m/%Y')}"
                    + (f" · Diario: {wiz.journal_id.name}" if wiz.journal_id else ""), f["sub"])
        return 3

    def generate_xlsx_report(self, workbook, data, objs):
        wiz = objs[0]
        f = self._formats(workbook)
        moves = wiz._moves()

        por_diario = {}
        for move in moves:
            debit, credit = wiz._move_amounts(move)
            por_diario.setdefault(move.journal_id, []).append((move, debit, credit))

        resumen = workbook.add_worksheet("Resumen")
        self._summary(resumen, wiz, f, por_diario, moves)
        detalle = workbook.add_worksheet("Detalle")
        self._detail(detalle, wiz, f, por_diario)

    # -- hoja resumen --------------------------------------------------
    def _summary(self, sheet, wiz, f, por_diario, moves):
        row = self._header(sheet, wiz, f, "Auditoría de diario")
        headers = ["Diario", "Tipo", "Documentos", "Por revisar", "Deber", "Haber", "Balance"]
        for col, name in enumerate(headers):
            sheet.write(row, col, name, f["head"])
        row += 1

        tot_docs = tot_rev = 0
        tot_debe = tot_haber = 0.0
        for journal in sorted(por_diario, key=lambda j: j.sequence or 0):
            rows = por_diario[journal]
            debe = sum(d for _m, d, _h in rows)
            haber = sum(h for _m, _d, h in rows)
            revisar = sum(1 for _m, d, h in rows if abs(d - h) > 0.01)
            sheet.write(row, 0, journal.name, f["cell"])
            sheet.write(row, 1, journal.type, f["cell"])
            sheet.write_number(row, 2, len(rows), f["cell"])
            sheet.write_number(row, 3, revisar, f["alert"] if revisar else f["cell"])
            sheet.write_number(row, 4, round(debe, 2), f["money"])
            sheet.write_number(row, 5, round(haber, 2), f["money"])
            sheet.write_number(row, 6, round(debe - haber, 2), f["money"])
            row += 1
            tot_docs += len(rows)
            tot_rev += revisar
            tot_debe += debe
            tot_haber += haber

        sheet.write(row, 0, "TOTAL", f["label_bold"])
        sheet.write(row, 1, "", f["label_bold"])
        sheet.write_number(row, 2, tot_docs, f["label_bold"])
        sheet.write_number(row, 3, tot_rev, f["label_bold"])
        sheet.write_number(row, 4, round(tot_debe, 2), f["money_bold"])
        sheet.write_number(row, 5, round(tot_haber, 2), f["money_bold"])
        sheet.write_number(row, 6, round(tot_debe - tot_haber, 2), f["money_bold"])
        row += 2

        row = self._controls(sheet, wiz, f, row, por_diario, moves)

    def _controls(self, sheet, wiz, f, row, por_diario, moves):
        sheet.write(row, 0, "CONTROLES", f["head"])
        for col in range(1, 7):
            sheet.write(row, col, "", f["head"])
        row += 1

        desbalanceados = sum(1 for rows in por_diario.values()
                             for (_m, d, h) in rows if abs(d - h) > 0.01)
        sheet.write(row, 0, "Asientos desbalanceados (debe ≠ haber)", f["cell"])
        sheet.write_number(row, 2, desbalanceados, f["alert"] if desbalanceados else f["cell"])
        row += 1

        borradores = self.env["account.move"].search_count([
            ("company_id", "=", wiz.company_id.id),
            ("state", "=", "draft"),
            ("date", ">=", wiz.date_from),
            ("date", "<=", wiz.date_to),
        ] + ([("journal_id", "=", wiz.journal_id.id)] if wiz.journal_id else []))
        sheet.write(row, 0, "Borradores en el período", f["cell"])
        sheet.write_number(row, 2, borradores, f["alert"] if borradores else f["cell"])
        row += 1

        for journal, (cantidad, desde, hasta) in self._gaps(por_diario).items():
            sheet.write(row, 0, f"Huecos de secuencia — {journal}", f["cell"])
            sheet.write(row, 1, f"{desde}…{hasta}", f["cell"])
            sheet.write_number(row, 2, cantidad, f["alert"])
            row += 1
        return row

    def _gaps(self, por_diario):
        """Números faltantes en la secuencia de comprobantes, por diario."""
        res = {}
        for journal, rows in por_diario.items():
            nums = set()
            for move, _d, _h in rows:
                digitos = re.findall(r"(\d+)\s*$", (move.name or "").strip())
                if digitos:
                    nums.add(int(digitos[0]))
            if not nums:
                continue
            faltantes = [n for n in range(min(nums), max(nums) + 1) if n not in nums]
            if faltantes:
                res[journal.name] = (len(faltantes), min(nums), max(nums))
        return res

    # -- hoja detalle --------------------------------------------------
    def _detail(self, sheet, wiz, f, por_diario):
        row = self._header(sheet, wiz, f, "Detalle de asientos")
        sheet.set_column(2, 2, 12)
        sheet.set_column(3, 3, 30)
        for col, name in enumerate(["Diario", "Asiento", "Fecha", "Tercero", "Debe", "Haber", "Diferencia", "Estado"]):
            sheet.write(row, col, name, f["head"])
        row += 1

        for journal in sorted(por_diario, key=lambda j: j.sequence or 0):
            for move, debe, haber in sorted(por_diario[journal], key=lambda t: (t[0].date, t[0].name or "")):
                sheet.write(row, 0, journal.name, f["cell"])
                sheet.write(row, 1, move.name or "", f["cell"])
                sheet.write(row, 2, move.date.strftime("%d/%m/%Y") if move.date else "", f["cell"])
                sheet.write(row, 3, move.partner_id.display_name if move.partner_id else "", f["cell"])
                sheet.write_number(row, 4, round(debe, 2), f["money"])
                sheet.write_number(row, 5, round(haber, 2), f["money"])
                diff = round(debe - haber, 2)
                sheet.write_number(row, 6, diff, f["alert"] if abs(diff) > 0.01 else f["money"])
                sheet.write(row, 7, move.state, f["cell"])
                row += 1
