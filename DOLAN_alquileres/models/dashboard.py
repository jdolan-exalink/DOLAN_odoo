"""KPI strip de alquileres (patrón EE): Hoy, Pickups, Returns, Tarde,
Por confirmar, Por facturar."""
from datetime import date


def kpis(env):
    hoy = date.today()
    hoys = hoy.isoformat()
    C = env["dolan.alquiler.contrato"]
    base = [("state", "!=", "cancelado")]
    hoy_retiros = C.search_count(base + [("fecha_pickup", ">=", f"{hoys} 00:00:00"),
                                         ("fecha_pickup", "<=", f"{hoys} 23:59:59")])
    if not hoy_retiros:
        hoy_retiros = C.search_count(base + [("fecha_inicio", "=", hoys)])
    pickups = C.search_count(base + [("estado_ops", "=", "pendiente"),
                                     ("fecha_inicio", "<=", hoys)])
    returns = C.search_count(base + [("estado_ops", "=", "recolectada"),
                                     ("fecha_fin", "=", hoys)])
    tarde = C.search_count(base + [("estado_ops", "!=", "devuelta"),
                                   ("fecha_fin", "<", hoys),
                                   ("state", "!=", "finalizado")])
    por_confirmar = C.search_count([("state", "=", "borrador")])
    por_facturar = C.search_count([
        ("state", "in", ("activo", "finalizado")),
        "|",
        ("move_id", "=", False),
        ("move_id.state", "=", "draft"),
    ])
    return {
        "hoy": hoy_retiros, "pickups": pickups, "returns": returns,
        "tarde": tarde, "por_confirmar": por_confirmar, "por_facturar": por_facturar,
    }
