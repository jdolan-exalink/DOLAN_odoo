from odoo import api, SUPERUSER_ID


def post_init_hook(env):
    """Siembra los agentes DOLAN correspondientes a los dominios del sistema."""
    Agent = env["dolan.ai.agente"].sudo()
    existentes = set(Agent.search([]).mapped("name"))
    def mid(model):
        rec = env["ir.model"].sudo().search([("model", "=", model)], limit=1)
        return rec.id
    def crear_si_falta(name, vals):
        if name in existentes:
            return
        Agent.create(dict(vals, name=name))

    crear_si_falta("Asistente de contactos", {
        "proposito": "Eres un asistente de contactos de una PyME argentina. Ayudá a buscar, "
                     "contar y actualizar contactos (res.partner). Sé breve y concreto, en español. "
                     "Si no tenés acceso a lo que te piden, explicá la limitación y sugerí el paso más útil.",
        "sugerencias": "¿Cuántos contactos tengo?\nBuscá los últimos 5 contactos\n¿Qué proveedores empiezan con A?",
        "modelos_ids": [(6, 0, [mid("res.partner")])],
    })
    crear_si_falta("Asistente contable", {
        "proposito": "Eres un asistente contable. Podés consultar facturas, asientos y líneas "
                     "(account.move, account.move.line, account.tax) en modo LECTURA. Respondé con números "
                     "en formato argentino ($ 1.234,56) y en español. No podés modificar asientos: si te lo "
                     "piden, aclaralo y sugerí hacerlo manualmente.",
        "sugerencias": "¿Cuántas facturas hay este mes?\nÚltimas 5 facturas de venta\n¿Cuántas facturas sin CAE?",
        "modelos_ids": [(6, 0, [mid("account.move"), mid("account.move.line"), mid("account.tax")])],
    })
    crear_si_falta("Asistente de compras", {
        "proposito": "Eres un asistente de compras. Consultá órdenes de compra y proveedores "
                     "(purchase.order, purchase.order.line, res.partner) en modo lectura; podés crear y "
                     "actualizar contactos. Respondé en español, breve y accionable.",
        "sugerencias": "¿Cuántas órdenes de compra abiertas hay?\nÚltimos 5 proveedores\nPedidos por confirmar",
        "modelos_ids": [(6, 0, [mid("purchase.order"), mid("purchase.order.line"), mid("res.partner")])],
    })
    crear_si_falta("Asistente de operaciones", {
        "proposito": "Eres un asistente de operaciones (inventario/taller). Consultá transferencias, "
                     "existencias y turnos (stock.picking, stock.quant, dolan.taller.turno, "
                     "dolan.alquiler.contrato, dolan.suscripcion.suscripcion) en modo lectura. "
                     "Respondé en español con datos concretos.",
        "sugerencias": "¿Qué transferencias están pendientes?\nÚltimos 5 turnos de taller\nAlquileres activos",
        "modelos_ids": [(6, 0, [mid("stock.picking"), mid("stock.quant"), mid("dolan.taller.turno"),
                                mid("dolan.alquiler.contrato"), mid("dolan.suscripcion.suscripcion")])],
    })
    env.cr.commit() if hasattr(env.cr, "commit") else None
