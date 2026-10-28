"""Lookup de escaneo (v2): producto/embalaje, recoleccion (picking),
contacto y tipo de operacion. Lecturas sudo (multi-compania)."""


def _action_for(env, model_name):
    act = env["ir.actions.act_window"].sudo().search([
        ("res_model", "=", model_name), ("type", "ilike", "act_window"),
    ], order="id", limit=1)
    return act.id if act else False


def lookup(env, code):
    code = (code or "").strip()
    if not code:
        return {"ok": False, "error": "codigo_vacio"}
    Product = env["product.product"].sudo()
    product = Product.search([("barcode", "=", code)], limit=1)
    if not product:
        tmpl = env["product.template"].sudo().with_context(active_test=False).search(
            [("default_code", "=", code)], limit=1)
        product = tmpl.product_variant_id or tmpl.product_variant_ids[:1]
    if product:
        return _producto(env, product, code)

    # recoleccion / transferencia
    picking = env["stock.picking"].sudo().with_context(active_test=False).search([
        "|", ("name", "=", code), ("origin", "=", code),
    ], order="id desc", limit=1)
    if picking:
        return {"ok": True, "tipo": "picking", "titulo": picking.name,
                "detalle": f"{picking.partner_id.display_name or '—'} · {picking.picking_type_id.display_name} · {picking.state}",
                "action_id": _action_for(env, "stock.picking"), "code": code}

    # contacto (ref = codigo de cliente) o nombre exacto
    partner = env["res.partner"].sudo().with_context(active_test=False).search([
        "|", ("ref", "=", code), ("name", "=", code),
    ], limit=1)
    if partner:
        pend = env["stock.picking"].sudo().search_count([("partner_id", "=", partner.id), ("state", "not in", ("done", "cancel"))])
        return {"ok": True, "tipo": "partner", "titulo": partner.display_name,
                "detalle": f"Contacto · {pend} transferencias pendientes",
                "action_id": _action_for(env, "res.partner"), "code": code}

    # tipo de operacion (codigo interno, p.ej. IN/OUT)
    ptype = env["stock.picking.type"].sudo().search(["|", ("code", "=", code), ("name", "=", code)], limit=1)
    if ptype:
        return {"ok": True, "tipo": "operacion", "titulo": ptype.display_name,
                "detalle": f"Tipo de operación · {ptype.warehouse_id.display_name or '—'}",
                "action_id": _action_for(env, "stock.picking"), "code": code}

    return {"ok": False, "error": "no_encontrado", "code": code}


def _producto(env, product, code):
    quants = env["stock.quant"].sudo().search([
        ("product_id", "=", product.id),
        ("quantity", "!=", 0),
        ("location_id.usage", "!=", "inventory"),
    ])
    existencias = {}
    for q in quants:
        key = q.location_id.complete_name or q.location_id.display_name
        existencias[key] = round(existencias.get(key, 0) + q.quantity, 3)
    return {
        "ok": True, "tipo": "producto",
        "titulo": product.display_name,
        "detalle": f"SKU {product.default_code or '—'} · barras {product.barcode or '—'} · total {round(sum(existencias.values()), 3)} {product.uom_id.display_name}",
        "existencias": existencias,
        "total": round(sum(existencias.values()), 3),
        "action_id": False,
        "producto": {"id": product.id, "name": product.display_name,
                     "barcode": product.barcode or "", "sku": product.default_code or "",
                     "unidad": product.uom_id.display_name, "categoria": product.categ_id.display_name},
        "code": code,
    }
