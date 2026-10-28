"""KPIs de suscripciones: MRR, activas, proximas 7d, vencidas."""


def kpis(env):
    from datetime import date, timedelta
    hoy = date.today()
    activas = env["dolan.suscripcion.suscripcion"].search([("state", "=", "activa")])
    mrr = 0.0
    for s in activas:
        ciclo = s.plan_id.ciclo_dias or 30
        mrr += (s.plan_id.precio or 0.0) * 30.0 / ciclo
    fin = (hoy + timedelta(days=7)).isoformat()
    proximas = len(activas.filtered(lambda s: s.proxima and hoy.isoformat() <= s.proxima.isoformat() <= fin))
    vencidas = len(activas.filtered(lambda s: s.proxima and s.proxima <= hoy))
    return {
        "mrr": round(mrr, 2),
        "activas": len(activas),
        "proximas_7d": proximas,
        "por_facturar": vencidas,
        "planes": env["dolan.suscripcion.plan"].search_count([("activo", "=", True)]),
    }
