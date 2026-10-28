"""OCR de compras vía ChatGPT (S2): imagen → JSON de factura → borrador.

Seguridad (ítem 2): sin secretos en BD (usa el token del device flow ya
conectado), payload truncado, respuesta esperada = JSON estricto.
"""
import base64
import json
import re

from odoo import http  # noqa: F401 (reservado para helpers futuros)


OCR_PROMPT = (
    "Sos un extractor de datos de comprobantes argentinos. Devolvé SOLO un JSON "
    "válido con esta estructura (sin texto extra): "
    '{"proveedor": str, "cuit": str, "fecha": "YYYY-MM-DD", "tipo_doc": str, '
    '"numero": str, "total": number, "lineas": [{"descripcion": str, "cantidad": number, "precio": number}]}. '
    "Si un dato no figura usá null o lista vacía."
)

MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_PDF_PAGES = 3
PDF_TEXT_MIN = 60  # chars mínimos para considerar un PDF "digital"


def pdf_to_images(pdf_bytes):
    """PDF -> lista de data-URL PNG (raster, para PDFs escaneados).

    Requiere pypdfium2 (instalado en el contenedor). Devuelve [] si no
    está disponible o el PDF no se puede abrir.
    """
    try:
        import pypdfium2 as pdfium
    except ImportError:
        return []
    try:
        doc = pdfium.PdfDocument(pdf_bytes)
        out = []
        for i, page in enumerate(doc):
            if i >= MAX_PDF_PAGES:
                break
            bitmap = page.render(scale=2.0)
            pil = bitmap.to_pil()
            import io
            buf = io.BytesIO()
            pil.save(buf, format="PNG")
            out.append("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())
        doc.close()
        return out
    except Exception:  # noqa: BLE001 — PDF corrupto o protegido
        return []


def pdf_to_text(pdf_bytes):
    """Texto embebido del PDF (PDFs digitales de ARCA/facturadores)."""
    try:
        from pdfminer.high_level import extract_text
        import io
        return (extract_text(io.BytesIO(pdf_bytes)) or "").strip()
    except Exception:  # noqa: BLE001
        return ""


def build_ocr_text_body(text, prompt=OCR_PROMPT):
    """Body para PDFs digitales: el texto va como input_text (sin imagen)."""
    return {
        "model": "gpt-6-luna",
        "input": [{"role": "user", "content": [
            {"type": "input_text", "text": prompt + "\n\nTEXTO DEL COMPROBANTE:\n" + text[:12000]},
        ]}],
        "max_output_tokens": 1500,
        "stream": True,
        "store": False,
    }


def build_ocr_body(data_url, prompt=OCR_PROMPT):
    """Body del Responses API con imagen inline (data URL)."""
    return {
        "model": "gpt-6-luna",
        "input": [{"role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": data_url},
        ]}],
        "max_output_tokens": 1500,
        "stream": True,
        "store": False,
    }


def parse_ocr_text(text):
    """JSON robusto desde la respuesta del modelo (tolera fences)."""
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None
    if not isinstance(data, dict):
        return None
    if not any(k in data for k in ("proveedor", "fecha", "numero", "total", "lineas")):
        return None
    return data


def extract_from_source(env, source):
    """source: {"kind": "image", "data": data_url} o {"kind": "pdf", "bytes": b"}.

    PDF: intenta raster (pypdfium2) → vision; si no rasteriza pero hay
    texto embebido → modo texto (input_text). Devuelve dict parseado.
    """
    from . import chatgpt_oauth as cgo
    tokens = cgo.get_valid_tokens()
    if not tokens:
        return {"ok": False, "error": "no_conectado"}
    if tokens.get("needs_reconnect"):
        return {"ok": False, "error": "token_vencido_reconectar"}
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    if tokens.get("account_id"):
        headers["ChatGPT-Account-Id"] = tokens["account_id"]
    body = None
    if source["kind"] == "pdf":
        pages = pdf_to_images(source["bytes"])
        if pages:
            body = build_ocr_body(pages[0])
        else:
            text = pdf_to_text(source["bytes"])
            if len(text) >= PDF_TEXT_MIN:
                body = build_ocr_text_body(text)
            else:
                return {"ok": False, "error": "pdf_sin_soporte",
                        "detalle": "PDF escaneado sin rasterizador y sin texto embebido"}
    else:
        body = build_ocr_body(source["data"])
    import requests
    try:
        resp = requests.post(
            cgo.CODEX_API_ENDPOINT, json=body,
            headers=headers, timeout=(15, 180), stream=True)
    except requests.RequestException:
        return {"ok": False, "error": "http_request_exception"}
    if resp.status_code not in (200, 201):
        return {"ok": False, "error": f"http_{resp.status_code}", "detalle": resp.text[:200]}
    parts = []
    try:
        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if not payload or payload == "[DONE]":
                continue
            try:
                ev = json.loads(payload)
            except ValueError:
                continue
            etype = ev.get("type", "")
            if etype == "response.output_text.delta":
                parts.append(ev.get("delta", ""))
            elif etype == "response.output_text.done" and ev.get("text"):
                parts = [ev["text"]]
            elif etype in ("response.failed", "response.incomplete"):
                return {"ok": False, "error": "ocr_stream_failed"}
    except (requests.RequestException, OSError):
        return {"ok": False, "error": "ocr_stream_error"}
    parsed = parse_ocr_text("".join(parts))
    if not parsed:
        return {"ok": False, "error": "ocr_json_invalido", "texto": ("\n".join(parts))[:300]}
    return {"ok": True, "datos": parsed}


def map_to_draft(env, datos, default_partner_name=None, default_tax_xmlid="l10n_ar.iva_21"):
    """Mapea JSON OCR a valores de factura borrador (sin crear aún)."""
    lineas = []
    for ln in (datos.get("lineas") or [])[:50]:
        qty = ln.get("cantidad") or 1
        price = ln.get("precio") or 0
        try:
            qty, price = float(qty), float(price)
        except (TypeError, ValueError):
            continue
        if qty <= 0 or price <= 0:
            continue
        lineas.append({"name": (ln.get("descripcion") or "Item")[:140],
                       "quantity": qty, "price_unit": price})
    if not lineas:
        # sin líneas legibles: un total único
        total = datos.get("total")
        try:
            total = float(total)
        except (TypeError, ValueError):
            return {"ok": False, "error": "sin_lineas_ni_total"}
        lineas = [{"name": "Compra importada (OCR)", "quantity": 1, "price_unit": round(total, 2)}]
    partner_name = datos.get("proveedor") or default_partner_name or "Proveedor OCR"
    return {
        "ok": True,
        "vals": {
            "move_type": "in_invoice",
            "partner_name_suggest": partner_name,
            "invoice_date": datos.get("fecha"),
            "ref": datos.get("numero"),
            "ocr_meta": {
                "cuit": datos.get("cuit"), "tipo_doc": datos.get("tipo_doc"),
                "total": datos.get("total"),
            },
            "lineas": lineas,
            "default_tax_xmlid": default_tax_xmlid,
        },
    }


def create_draft(env, datos):
    """Crea la factura borrador completa (partner incluido si no existe)."""
    mapped = map_to_draft(env, datos)
    if not mapped.get("ok"):
        return mapped
    vals = mapped["vals"]
    Partner = env["res.partner"].sudo()
    partner = Partner.search([("name", "=", vals["partner_name_suggest"])], limit=1)
    if not partner:
        partner = Partner.create({"name": vals["partner_name_suggest"]})
    tax = env.ref(vals["default_tax_xmlid"], raise_if_not_found=False)
    tax_ids = [(6, 0, [tax.id])] if tax else []
    Move = env["account.move"].sudo()
    move = Move.create({
        "move_type": "in_invoice",
        "partner_id": partner.id,
        "ref": vals.get("ref") or "",
        "invoice_line_ids": [(0, 0, {
            "name": ln["name"], "quantity": ln["quantity"],
            "price_unit": ln["price_unit"], "tax_ids": tax_ids,
        }) for ln in vals["lineas"]],
    })
    return {"ok": True, "move_id": move.id, "move_name": move.name or ""}


def extract_from_image(env, data_url):
    """Compat: extracción desde imagen (data URL)."""
    return extract_from_source(env, {"kind": "image", "data": data_url})
