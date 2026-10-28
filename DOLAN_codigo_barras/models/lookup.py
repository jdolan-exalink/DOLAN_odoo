"""Lookup de producto por codigo de barras + existencias por ubicacion.

Sudo sobre los recordsets de lectura (Environment v20 no expone .sudo()):
el escaneo consulta productos/cantidades de cualquier compania.
"""


def lookup(env, code):
    code = (code or "").strip()
    if not code:
        return {"ok": False, "error": "codigo_vacio"}

    Product = env["product.product"].sudo()
    product = Product.search([("barcode", "=", code)], limit=1)

    if not product:
        # fallback por SKU: default_code vive en product.template (y su variante
        # puede estar archivada en datos migrados)
        tmpl = env["product.template"].sudo().with_context(active_test=False).search(
            [("default_code", "=", code)], limit=1)
        product = tmpl.product_variant_id
        if not product:
            product = tmpl.product_variant_ids[:1]

    if not product:
        return {"ok": False, "error": "no_encontrado", "code": code}

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
        "ok": True,
        "producto": {
            "id": product.id,
            "name": product.display_name,
            "barcode": product.barcode or "",
            "sku": product.default_code or "",
            "unidad": product.uom_id.display_name,
            "categoria": product.categ_id.display_name,
        },
        "existencias": existencias,
        "total": round(sum(existencias.values()), 3),
    }
