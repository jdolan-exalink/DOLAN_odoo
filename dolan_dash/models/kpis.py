from datetime import timedelta

from odoo import api, fields, models


def ar(n):
    """Formato argentino: 12.618.049,62"""
    s = f"{n:,.2f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


WIDGETS_POR_DEFECTO = "facturas,gastos,efectivo,por_cobrar,compras,nc,remitos,recepciones"


class DolanDash(models.TransientModel):
    _name = "dolan.dash"
    _description = "KPIs del dashboard operativo"

    @api.model
    def kpis(self):
        """KPIs del Home: widgets ordenados/habilitados por parametro de
        sistema (admin) y filtrados por permisos del usuario (por rol)."""
        now = fields.Datetime.now()
        hoy = now.date()
        mstart = hoy.replace(day=1)
        co = self.env.company
        moves = self.env["account.move"]
        base = [("company_id", "=", co.id), ("state", "=", "posted")]
        user = self.env.user

        can_account = (user.has_group("account.group_account_user")
                       or user.has_group("account.group_account_manager")
                       or user.has_group("base.group_system"))
        can_stock = (user.has_group("stock.group_stock_user")
                     or user.has_group("stock.group_stock_manager"))
        can_expense = (user.has_group("hr_expense.group_hr_expense_user")
                       or user.has_group("hr_expense.group_hr_expense_manager")
                       or user.has_group("base.group_system"))

        facturas = moves.search(base + [("move_type", "in", ("out_invoice", "out_refund")),
                                        ("invoice_date", ">=", mstart)])
        ncs = moves.search(base + [("move_type", "=", "out_refund"),
                                   ("invoice_date", ">=", mstart)])
        por_cobrar = moves.search(base + [("move_type", "in", ("out_invoice", "out_refund")),
                                          ("payment_state", "not in", ("paid", "reversed"))])
        por_pagar = moves.search(base + [("move_type", "=", "in_invoice"),
                                         ("payment_state", "not in", ("paid", "reversed"))])
        vencidas = por_pagar.filtered(lambda m: m.invoice_date_due and m.invoice_date_due < hoy)
        out_types = self.env["stock.picking.type"].search(
            [("company_id", "=", co.id), ("code", "=", "outgoing")])
        in_types = self.env["stock.picking.type"].search(
            [("company_id", "=", co.id), ("code", "=", "incoming")])
        remitos = self.env["stock.picking"].search(
            [("company_id", "=", co.id), ("state", "=", "done"),
             ("picking_type_id", "in", out_types.ids)])
        recepciones = self.env["stock.picking"].search(
            [("company_id", "=", co.id), ("state", "=", "done"),
             ("picking_type_id", "in", in_types.ids)])

        # Efectivo: saldo contable de las cuentas de los diarios banco/caja
        journals = self.env["account.journal"].search(
            [("company_id", "=", co.id), ("type", "in", ("bank", "cash"))])
        acc_ids = journals.mapped("default_account_id").ids
        saldo = 0.0
        if acc_ids:
            # Odoo20 cambio la sintaxis de agregados de read_group; poquitas
            # lineas de banco/caja: sumamos directo
            mlines = self.env["account.move.line"].search(
                [("company_id", "=", co.id), ("account_id", "in", acc_ids)])
            saldo = sum(mlines.mapped("balance"))

        # Gastos: gastos de hr expense registrados en el mes
        gasto_model = self.env["hr.expense"]
        gdom = [("date", ">=", mstart)]
        if "company_id" in gasto_model._fields:
            gdom.append(("company_id", "=", co.id))
        gastos_mes = gasto_model.search(gdom)

        data = {
            "efectivo": {
                "key": "efectivo", "label": "Efectivo",
                "valor": "$ " + ar(saldo),
                "hint": "bancos + caja (saldo contable)",
                "tag": "bg-secondary-subtle text-secondary",
            },
            "gastos": {
                "key": "gastos", "label": "Gastos",
                "valor": len(gastos_mes),
                "hint": "$ " + ar(sum(gastos_mes.mapped("total_amount"))) + " en el mes",
                "tag": "bg-orange-subtle text-warning",
            },
            "facturas": {
                "key": "facturas", "label": "Facturas del mes",
                "valor": len(facturas),
                "hint": "$ " + ar(sum(facturas.mapped("amount_total"))),
                "tag": "bg-primary-subtle text-primary",
            },
            "compras": {
                "key": "compras", "label": "Compras por pagar",
                "valor": len(por_pagar),
                "hint": "$ " + ar(sum(por_pagar.mapped("amount_residual")))
                        + " · " + str(len(vencidas)) + " vencidas",
                "tag": "bg-danger-subtle text-danger",
            },
            "por_cobrar": {
                "key": "por_cobrar", "label": "Por cobrar",
                "valor": len(por_cobrar),
                "hint": "$ " + ar(sum(por_cobrar.mapped("amount_residual"))),
                "tag": "bg-info-subtle text-info",
            },
            "nc": {
                "key": "nc", "label": "Notas de crédito",
                "valor": len(ncs),
                "hint": "emitidas en el mes",
                "tag": "bg-warning-subtle text-warning",
            },
            "remitos": {
                "key": "remitos", "label": "Remitos entregados",
                "valor": len(remitos),
                "hint": "histórico",
                "tag": "bg-success-subtle text-success",
            },
            "recepciones": {
                "key": "recepciones", "label": "Recepciones",
                "valor": len(recepciones),
                "hint": "ingresos de inventario",
                "tag": "bg-secondary-subtle text-secondary",
            },
        }
        # filtro por permisos (por rol): quien no tiene el modulo no ve el widget
        gate = {
            "compras": can_account, "por_cobrar": can_account,
            "remitos": can_stock, "recepciones": can_stock,
            "efectivo": can_account, "gastos": can_expense,
            "facturas": True, "nc": True,
        }
        orden = self.env["ir.config_parameter"].sudo().get_str(
            "dolan.ui.widgets", WIDGETS_POR_DEFECTO)
        keys = [k.strip() for k in orden.split(",") if k.strip()]
        widgets = [data[k] for k in keys if k in data and gate.get(k, True)]
        return {"company": co.name, "mes": now.strftime("%m/%Y"), "widgets": widgets}

    @api.model
    def detalle(self):
        """Filas detalladas bajo los KPIs (estilo tabla del prototipo)."""
        co = self.env.company
        hoy = fields.Datetime.now().date()
        moves = self.env["account.move"]
        base = [("company_id", "=", co.id), ("state", "=", "posted")]

        def read(dom, order, limit):
            return moves.search_read(dom, ["name", "partner_id", "invoice_date",
                                           "invoice_date_due", "amount_total",
                                           "amount_residual", "move_type"],
                                     order=order, limit=limit)

        pend = []
        for r in read(base + [("move_type", "=", "in_invoice"),
                              ("payment_state", "not in", ("paid", "reversed"))],
                      "invoice_date_due asc, name", 10):
            due = r["invoice_date_due"]
            pend.append({
                "id": r["id"],
                "num": r["name"], "tercero": (r["partner_id"] or [False, "—"])[1],
                "fecha": (due or r["invoice_date"] or "").strftime("%d/%m/%Y"),
                "estado": "Vencida" if (due and due < hoy) else "Pendiente",
                "monto": ar(r["amount_residual"] or r["amount_total"] or 0),
            })

        pag = []
        for r in read(base + [("move_type", "=", "in_invoice"),
                              ("payment_state", "in", ("paid", "reversed"))],
                      "invoice_date desc, name", 10):
            pag.append({
                "num": r["name"], "tercero": (r["partner_id"] or [False, "—"])[1],
                "fecha": (r["invoice_date"] or "").strftime("%d/%m/%Y"),
                "estado": "Pagada",
                "monto": ar(r["amount_total"] or 0),
            })

        mstart = hoy.replace(day=1)
        fact = []
        for r in read(base + [("move_type", "in", ("out_invoice", "out_refund")),
                              ("invoice_date", ">=", mstart)],
                      "invoice_date desc, name", 10):
            fact.append({
                "num": r["name"], "tercero": (r["partner_id"] or [False, "—"])[1],
                "fecha": (r["invoice_date"] or "").strftime("%d/%m/%Y"),
                "estado": "NC" if r["move_type"] == "out_refund" else "Factura",
                "monto": ar(r["amount_total"] or 0),
            })

        nc = []
        for r in read(base + [("move_type", "=", "out_refund"),
                              ("invoice_date", ">=", mstart)],
                      "invoice_date desc, name", 10):
            nc.append({
                "num": r["name"], "tercero": (r["partner_id"] or [False, "—"])[1],
                "fecha": (r["invoice_date"] or "").strftime("%d/%m/%Y"),
                "monto": ar(r["amount_total"] or 0),
            })

        rem = []
        picks = self.env["stock.picking"].search_read(
            [("company_id", "=", co.id), ("state", "=", "done"),
             ("picking_type_id.code", "=", "outgoing")],
            ["name", "partner_id", "scheduled_date", "date_done"],
            order="date_done desc, name", limit=10)
        for r in picks:
            rem.append({
                "num": r["name"],
                "tercero": (r["partner_id"] or [False, "—"])[1],
                "fecha": (r["date_done"] or r["scheduled_date"] or "").strftime("%d/%m/%Y"),
                "monto": "",
            })
        return {"por_pagar": pend, "pagadas": pag, "facturas": fact,
                "nc": nc, "remitos": rem}

    @api.model
    def serie(self, nombre):
        """Serie de 6 meses para el grafico de la seccion activa."""
        co = self.env.company
        hoy = fields.Datetime.now().date()
        labels, desde = [], hoy.replace(day=1)
        for _ in range(6):
            labels.insert(0, desde.strftime("%m/%y"))
            mes_anterior = desde.replace(day=1) - timedelta(days=1)
            desde = mes_anterior.replace(day=1)

        base = [("company_id", "=", co.id), ("state", "=", "posted")]

        def serie_moves(dom, acum="amount_total"):
            reads = self.env["account.move"].search_read(
                dom, ["invoice_date", acum], order="invoice_date", limit=2000)
            buckets = {l: 0.0 for l in labels}
            for r in reads:
                d = r["invoice_date"]
                if d:
                    buckets.setdefault(d.strftime("%m/%y"), 0.0)
                    buckets[d.strftime("%m/%y")] += r.get(acum) or 0
            return [round(buckets.get(l, 0.0), 2) for l in labels]

        if nombre == "facturas":
            vals = serie_moves(base + [("move_type", "in", ("out_invoice", "out_refund"))])
            titulo = "Facturas (monto, 6 meses)"
        elif nombre == "nc":
            vals = serie_moves(base + [("move_type", "=", "out_refund")])
            titulo = "Notas de credito (monto, 6 meses)"
        elif nombre == "compras":
            vals = serie_moves(base + [("move_type", "=", "in_invoice")])
            titulo = "Compras (monto, 6 meses)"
        elif nombre == "efectivo":
            journals = self.env["account.journal"].search(
                [("company_id", "=", co.id), ("type", "in", ("bank", "cash"))])
            acc_ids = journals.mapped("default_account_id").ids
            reads = self.env["account.move.line"].search_read(
                [("company_id", "=", co.id), ("account_id", "in", acc_ids)],
                ["date", "balance"], order="date", limit=5000) if acc_ids else []
            buckets = {l: 0.0 for l in labels}
            for r in reads:
                d = r["date"]
                if d:
                    buckets.setdefault(d.strftime("%m/%y"), 0.0)
                    buckets[d.strftime("%m/%y")] += r.get("balance") or 0
            vals = [round(buckets.get(l, 0.0), 2) for l in labels]
            titulo = "Efectivo (variacion, 6 meses)"
        elif nombre == "gastos":
            gdom = [("date", ">=", labels and hoy.replace(day=1))]
            gasto_model = self.env["hr.expense"]
            if "company_id" in gasto_model._fields:
                gdom = [("company_id", "=", co.id)]
            reads = gasto_model.search_read(
                [("date", ">=", hoy.replace(day=1) - timedelta(days=180))]
                + ([("company_id", "=", co.id)] if "company_id" in gasto_model._fields else []),
                ["date", "total_amount"], order="date", limit=2000)
            buckets = {l: 0.0 for l in labels}
            for r in reads:
                d = r["date"]
                if d:
                    buckets.setdefault(d.strftime("%m/%y"), 0.0)
                    buckets[d.strftime("%m/%y")] += r.get("total_amount") or 0
            vals = [round(buckets.get(l, 0.0), 2) for l in labels]
            titulo = "Gastos (monto, 6 meses)"
        elif nombre == "por_cobrar":
            vals = serie_moves(base + [("move_type", "in", ("out_invoice", "out_refund")),
                                       ("payment_state", "not in", ("paid", "reversed"))],
                               acum="amount_residual")
            titulo = "Por cobrar (saldo, 6 meses)"
        else:
            code = "incoming" if nombre == "recepciones" else "outgoing"
            reads = self.env["stock.picking"].search_read(
                [("company_id", "=", co.id), ("state", "=", "done"),
                 ("picking_type_id.code", "=", code)],
                ["date_done"], order="date_done", limit=2000)
            buckets = {l: 0 for l in labels}
            for r in reads:
                d = r["date_done"]
                if d:
                    k = d.date().strftime("%m/%y")
                    buckets[k] = buckets.get(k, 0) + 1
            vals = [buckets.get(l, 0) for l in labels]
            titulo = ("Recepciones" if code == "incoming" else "Remitos") + " (cantidad, 6 meses)"
        top = max(max(vals), 1)
        cols = [{"label": l, "valor": ar(v), "pct": max(round(100 * v / top), 2)}
                for l, v in zip(labels, vals)]
        return {"titulo": titulo, "cols": cols}
