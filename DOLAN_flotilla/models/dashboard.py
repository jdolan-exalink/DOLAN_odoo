"""KPIs de flotilla (v1): contratos por vencer, vehículos activos, costos del mes."""
from datetime import date, timedelta


def _primer_dia_mes(d):
    return d.replace(day=1)


def kpis(env):
    hoy = date.today()
    fin_mes = (hoy.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    V = env["fleet.vehicle"]
    LC = env["fleet.vehicle.log.contract"]
    vehiculos = V.search_count([])
    ventana = (hoy + timedelta(days=30)).isoformat()
    contratos_por_vencer = LC.search_count([
        ("expiration_date", ">=", hoy.isoformat()),
        ("expiration_date", "<=", ventana),
    ])
    vencidos = LC.search_count([("expiration_date", "<", hoy.isoformat())])
    inicio = _primer_dia_mes(hoy).isoformat()
    # Odoo20: fleet.vehicle.log.fuel y log.odometer ya no existen;
    # costos del mes = services (amount) + contratos (amount)
    services = env["fleet.vehicle.log.services"].search([
        ("create_date", ">=", inicio)
    ])
    costo_services = sum(services.mapped("amount"))
    contratos_mes = LC.search([("start_date", ">=", inicio)])
    costo_contratos = sum(contratos_mes.mapped("amount"))
    return {
        "vehiculos": vehiculos,
        "contratos_por_vencer_30d": contratos_por_vencer,
        "contratos_vencidos": vencidos,
        "costo_contratos_mes": round(costo_contratos, 2),
        "costo_services_mes": round(costo_services, 2),
        "hoy": hoy.isoformat(),
    }
