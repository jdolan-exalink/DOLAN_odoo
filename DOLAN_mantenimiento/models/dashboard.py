"""KPIs de mantenimiento (v1): OTs abiertas, prioridad, atrasos, equipos."""
from datetime import date, timedelta


def kpis(env):
    R = env["maintenance.request"]
    hoy = date.today()
    abiertas = R.search_count([("stage_id.fold", "=", False)])
    criticas = R.search_count([("stage_id.fold", "=", False), ("priority", "in", ("3", "4"))])
    atrasadas = R.search_count([
        ("stage_id.fold", "=", False),
        ("schedule_date", "!=", False),
        ("schedule_date", "<", hoy.isoformat()),
    ])
    semana = (hoy + timedelta(days=7)).isoformat()
    proximas = R.search_count([
        ("stage_id.fold", "=", False),
        ("schedule_date", ">=", hoy.isoformat()),
        ("schedule_date", "<=", semana),
    ])
    equipos = env["maintenance.equipment"].search_count([])
    return {
        "ot_abiertas": abiertas,
        "ot_criticas": criticas,
        "ot_atrasadas": atrasadas,
        "ot_proximas_7d": proximas,
        "equipos": equipos,
        "hoy": hoy.isoformat(),
    }
