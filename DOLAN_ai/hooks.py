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
        # Orden de carga: DOLAN_ai entra antes que DOLAN_taller/alquileres/... y
        # mid() devuelve False para esos modelos -> [(6,0,[False])] truena el
        # registry ("Invalid falsy real id"). Se filtran los falsos y, si no
        # queda ninguno, no se crea el agente (otra pasada lo completa).
        mm = vals.get("modelos_ids")
        if mm and isinstance(mm[0], (list, tuple)) and mm[0][0] == 6:
            validos = [i for i in mm[0][2] if i]
            if not validos:
                return
            vals["modelos_ids"] = [(6, 0, validos)]
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


def post_init_prompts(env):
    """Biblioteca de prompts funcionales (resúmenes periódicos)."""
    Agent = env["dolan.ai.agente"].sudo()
    Prompt = env["dolan.ai.prompt"].sudo()
    if Prompt.search_count([]):
        return
    def mid(model):
        return env["ir.model"].sudo().search([("model", "=", model)], limit=1).id
    ag_cont = Agent.search([("name", "=", "Asistente contable")], limit=1)
    if ag_cont:
        Prompt.create({
            "agente_id": ag_cont.id, "sequence": 10,
            "name": "Resumen de facturación por empresa (semana)",
            "prompt": "Generá un resumen de facturación de la SEMANA en curso por cada compañía: "
                      "total emitido, cantidad de facturas, total de notas de crédito. "
                      "Usá account.move (out_invoice, out_refund) posted de los últimos 7 días. "
                      "Formato: una línea por empresa con montos en $ argentino y una conclusión de 1 línea.",
        })
        Prompt.create({
            "agente_id": ag_cont.id, "sequence": 20,
            "name": "Resumen de facturación por empresa (mes)",
            "prompt": "Generá un resumen de facturación del MES en curso por compañía: total emitido, "
                      "NC emitidas, facturas sin CAE (l10n_ar_fiscal_auth_code vacío) y top 3 clientes por monto. "
                      "Formato tabla markdown + conclusión breve.",
        })
        Prompt.create({
            "agente_id": ag_cont.id, "sequence": 30,
            "name": "Facturas vencidas por cobrar",
            "prompt": "Listá las facturas de venta posted con importe por cobrar > 0 (amount_residual > 0), "
                      "ordenadas por fecha de vencimiento ascendente, con cliente, monto y días de atraso. "
                      "Cerrá con el total a cobrar.",
        })
    ag_ops = Agent.search([("name", "=", "Asistente de operaciones")], limit=1)
    if ag_ops:
        Prompt.create({
            "agente_id": ag_ops.id, "sequence": 10,
            "name": "Transferencias pendientes de la semana",
            "prompt": "Listá las transferencias (stock.picking) no done/cancel con fecha prevista de los "
                      "próximos 7 días, agrupadas por tipo de operación, con cantidad de bultos y partner. "
                      "Cerrá con recomendación de prioridades.",
        })
    ag_comp = Agent.search([("name", "=", "Asistente de compras")], limit=1)
    if ag_comp:
        Prompt.create({
            "agente_id": ag_comp.id, "sequence": 10,
            "name": "Órdenes de compra por confirmar",
            "prompt": "Listá las órdenes de compra en estado borrador/enviada con total, proveedor y fecha "
                      "límite. Cerrá con las 3 más urgentes y por qué.",
        })
    env.cr.commit()
