"""KPIs contables v1: IVA del mes (líneas de impuesto), emitido/recibido del mes."""
from datetime import date


def _rango_mes(hoy):
    return hoy.replace(day=1).isoformat(), hoy.isoformat()


def kpis(env, hoy=None):
    hoy = hoy or date.today()
    ini, fin = _rango_mes(hoy)
    base = [("date", ">=", ini), ("date", "<=", fin), ("state", "=", "posted")]
    emitidas = env["account.move"].search_count(base + [("move_type", "=", "out_invoice")])
    recibidas = env["account.move"].search_count(base + [("move_type", "=", "in_invoice")])
    monto_emitido = sum(env["account.move"].search(base + [("move_type", "=", "out_invoice")]).mapped("amount_total"))
    monto_recibido = sum(env["account.move"].search(base + [("move_type", "=", "in_invoice")]).mapped("amount_total"))
    # IVA = líneas de impuesto (tax_line_id) del mes, balance negativo = débito
    aml = env["account.move.line"].search([("date", ">=", ini), ("date", "<=", fin), ("tax_line_id", "!=", False), ("move_id.state", "=", "posted")])
    iva_debito = -sum(aml.filtered(lambda l: l.balance < 0).mapped("balance"))
    iva_credito = sum(aml.filtered(lambda l: l.balance > 0).mapped("balance"))
    return {
        "emitidas": emitidas,
        "recibidas": recibidas,
        "monto_emitido": round(monto_emitido, 2),
        "monto_recibido": round(monto_recibido, 2),
        "iva_debito": round(iva_debito, 2),
        "iva_credito": round(iva_credito, 2),
        "iva_liquidado": round(iva_debito - iva_credito, 2),
        "hoy": hoy.isoformat(),
    }
