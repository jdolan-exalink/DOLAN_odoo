"""Conciliación automática de bancos (sin IAP/EE):
1. importar_extracto: CSV del banco -> statement + lines.
2. conciliar: matching de cada line sin conciliar contra amls abiertas de
   deudores/acreedores (partner, importe residual, referencia), con
   reconcile() del core. Ambiguo => se deja para el widget manual.
"""
import csv
import io

AMOUNT_EPS = 0.01


def _to_float(raw):
    """Convierte importes ambiguos: '1.234,56' | '1234.56' | '1,234.56'."""
    raw = (raw or "").replace("$", "").replace(" ", "").strip()
    if not raw:
        return 0.0
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            raw = raw.replace(".", "").replace(",", ".")   # 1.234,56
        else:
            raw = raw.replace(",", "")                     # 1,234.56
    elif "," in raw:
        raw = raw.replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _journal(env, company_id=None):
    j = env["account.journal"].sudo().search(
        [("type", "=", "bank")] + ([("company_id", "=", company_id)] if company_id else []), limit=1)
    return j


def importar_extracto(env, csv_text, journal_id=None, nombre="Extracto importado"):
    """CSV: fecha,referencia,debito,credito[,partner]. Crea statement + lines."""
    j = env["account.journal"].sudo().browse(journal_id) if journal_id else _journal(env)
    if not j:
        return {"ok": False, "error": "sin_diario_bancario"}
    reader = csv.reader(io.StringIO(csv_text.strip()))
    rows = [r for r in reader if r and any(x.strip() for x in r)]
    if not rows:
        return {"ok": False, "error": "csv_vacio"}
    # detectar encabezado
    if not rows[0][0].lower().startswith(("20", "19")):
        rows = rows[1:]
    st = env["account.bank.statement"].sudo().create({
        "journal_id": j.id, "date": None, "name": nombre,
    })
    creadas = 0
    for r in rows:
        try:
            fecha = r[0].strip()
            ref = r[1].strip() if len(r) > 1 else ""
            debito = _to_float(r[2]) if len(r) > 2 else 0.0
            credito = _to_float(r[3]) if len(r) > 3 else 0.0
        except (ValueError, IndexError):
            continue
        amount = (credito or 0.0) - (debito or 0.0)
        if abs(amount) < AMOUNT_EPS:
            continue
        partner = False
        if len(r) > 4 and r[4].strip():
            partner = env["res.partner"].sudo().search([("name", "=", r[4].strip())], limit=1)
        env["account.bank.statement.line"].sudo().create({
            "statement_id": st.id, "amount": amount, "date": fecha,
            "payment_ref": ref or nombre, "partner_id": partner.id if partner else False,
        })
        creadas += 1
    return {"ok": True, "statement_id": st.id, "lineas": creadas}


def _cuenta_partner(env, partner, amount, company):
    """Cuenta de deudor (cobros) o acreedor (pagos) del partner."""
    if not partner:
        return None
    prop = "property_account_receivable_id" if amount > 0 else "property_account_payable_id"
    cuenta = partner.sudo().with_company(company)[prop] or partner.sudo()[prop]
    return cuenta or None


def _candidatos(env, cuenta, partner, amount):
    """Amls abiertas compatibles: cuenta del partner, residual ~ importe."""
    if not cuenta:
        return []
    cands = env["account.move.line"].sudo().search([
        ("account_id", "=", cuenta.id),
        ("reconciled", "=", False),
        ("parent_state", "=", "posted"),
    ], limit=50)
    out = []
    for a in cands:
        if partner and a.partner_id and a.partner_id.id != partner.id:
            continue
        if abs(a.amount_residual - abs(amount)) > AMOUNT_EPS:
            continue
        out.append(a)
    return out


def conciliar(env, dias=90, journal_id=None):
    """Motor: partner (line o por ref) + importe residual exacto -> reconcile()."""
    from datetime import date, timedelta
    desde = (date.today() - timedelta(days=dias)).isoformat()
    lines = env["account.bank.statement.line"].sudo().search(
        [("is_reconciled", "=", False), ("date", ">=", desde)]
        + ([("journal_id", "=", journal_id)] if journal_id else []),
        order="date")
    res = {"lineas": len(lines), "conciliadas": 0, "ambiguas": 0, "sin_candidato": 0}
    for line in lines:
        partner = line.partner_id
        if not partner:
            # guess por referencia: token del ref que matchee un partner por nombre
            ref = (line.payment_ref or "").strip()
            if len(ref) >= 4:
                partner = env["res.partner"].sudo().search(
                    [("name", "ilike", ref[:25])], limit=1)
        # contar candidatos sobre la cuenta del partner SIN tocar el asiento
        cands = _candidatos(env, _cuenta_partner(env, partner, line.amount,
                                                 line.journal_id.company_id),
                            partner, line.amount)
        if not cands:
            res["sin_candidato"] += 1
            continue
        if len(cands) > 1:
            res["ambiguas"] += 1
            continue
        try:
            # único candidato: reasignar la counterpart del asiento del banco a la
            # cuenta del partner (como hace el widget manual) y conciliar
            counterpart = (line.move_id.line_ids - line.move_id.line_ids.filtered(
                lambda l: l.account_id == line.journal_id.default_account_id))
            aml_st = counterpart.filtered(
                lambda l: l.account_id.account_type in ("asset_receivable", "liability_payable"))
            aml_st = (aml_st or counterpart)[:1]
            aml_st.account_id = cands[0].account_id
            aml_st = (line.move_id.line_ids - line.move_id.line_ids.filtered(
                lambda l: l.account_id == line.journal_id.default_account_id)).filtered(
                lambda l: l.account_id == cands[0].account_id)[:1]
            (aml_st + cands[0]).reconcile()
            res["conciliadas"] += 1
        except Exception as exc:  # noqa: BLE001
            res.setdefault("errores", []).append(f"{line.id}: {exc.__class__.__name__}")
            res["sin_candidato"] += 1
    return res
