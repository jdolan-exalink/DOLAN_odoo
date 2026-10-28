# DOLAN gaps finales — Taller, Declaración fiscal, OCR, IA-agentes

Estado: en construcción (orden L27). Specs verbatim en ## Log; decisions L27a-d.

## Specs

- **S1** (verbatim L27a): construir DOLAN_taller, Declaración fiscal AR, OCR compras (F4), IA-agentes v1.
- **S2** (verbatim L27b): OCR = motor ChatGPT (cloud) con el token ya conectado.
- **S3** (verbatim L27c): IA-agentes v1 con tool-loop, permisos por herramienta (ítem 2 de seguridad: sin secretos en BD/repo, allowlist de modelos, sin borrado masivo).
- **S4** (verbatim L27d): F5 hito 2 después de los gaps.

## Tasks

| ID | Spec | Módulo | Alcance v1 | Estado |
|---|---|---|---|---|
| T1 | S2 | DOLAN_ai | OCR compra: adjuntar imagen → ChatGPT vision (input_image) → JSON → factura borrador `in_invoice` con líneas; page + ruta /dolan_ai/ocr_scan; tests con mocks (json extract, mapeo partner/tax por defecto, fallo OCR) | en curso |
| T2 | S1 | DOLAN_declaracion | períodos fiscales (mes/año) + checklist cierre (IVA digital, ventas, compras, CAE pendientes) con estados; KPI page; tests | pend |
| T3 | S1 | DOLAN_taller | centros de trabajo tablet: OP activa, operador, registrar consumo, timer por operación, punto de control QC (usa DOLAN_calidad); tests | pend |
| T4 | S3 | DOLAN_ai | agentes v1: registro (nombre+chips), tool-loop JSON con allowlist (search_read/create), máx iteraciones, sin unlink, log de uso | pend |

## Log

- **L1** (verbatim): "haceme las preguntas para destrabar y podedr terminar todos los modulos" + respuestas L27a-d del plan (S1-S4).

## Log (continuación)

- **L2**: T1 OCR listo (commit 6de71f5): extract (input_image, gpt-6-luna, store:false) → parse JSON con claves de negocio → map (sin líneas usa total) → create_draft (partner por nombre, IVA21 default, líneas máx50). Ruta `/dolan_ai/ocr_scan` con preview→commit; UI con botón+file+preview. 22 tests ✓, browser ✓ (0 errs).
- **L3**: T2 DOLAN_declaracion listo (commit f718ca7): períodos con checklist base de 6 ítems, IVA del período (débito/crédito/saldo), CAE pendientes = `l10n_ar_fiscal_auth_code=False` (Odoo20 fiscal_ws), cierre con validación + chatter. 5 tests ✓, rail ✓, lista 0 errs.
- **L4**: T3 DOLAN_taller listo (commit 0ee430b): turnos por centro de trabajo con operador, pausar/reanudar/terminar + minutos live, materiales (consumo), controles QC ligados a DOLAN_calidad (M2O vía `_inherit` en taller — sin acoplar módulos), chatter. 6 tests ✓, rail 40 apps ✓, lista 0 errs.
- **L5**: T4 IA-agentes v1 listo (commit siguiente): modelo `dolan.ai.agente` (mail.thread), tool-loop con allowlist por agente (`search_read` / `create`), `WRITE_MODELS_LIMIT`, límites iter/regs, log de uso en chatter, UI chat en /dolan_ai. 31 tests ✓ (25 totales en stats con agentes incluidos, 0 fallos).
- **Gotchas**: `base.model_*` xmlids NO existen en v20 → buscar `ir.model` por `model`; `dolan.ai.agente` con mail.thread exige depends `mail` (registry CRITICAL si falta); dependencia cruzada de modelos se resuelve con `_inherit` en el módulo dependiente (patrón OCA), no M2O en el módulo base.

## Pendiente
- F5 hito 2 (S4): elevar matriz B→C (oscuro + rol no-admin) — aprobado hacer después de los gaps; los 4 gaps ya están cerrados → siguiente ciclo.
- Prueba REAL del OCR/agentes con tu ChatGPT (abrir /dolan_ai → Escanear compra con una foto real).

### L29 — Bugfix UX DOLAN AI reportado por el usuario (2026-10-28)

Verbatims: "cuando entramos a DOLAN AI perdemos la sidebar", "en agentes no tenemos nada y el chat le damos enviar y no hace nada", "escanear compra no hace nada", "compras no veo subir factura OCR".

**Causas raíz y fixes:**
1. **Rail perdido**: `/dolan_ai` era página HTTP suelta (sin webclient) → mini-rail clonado inyectado en la página (load_menus por JSON-RPC + markup/estilos del tema). Verificado: 415 items de rail en la página, 0 errores consola.
2. **Agentes vacíos + chat sin efecto**: doble causa — (a) no existían agentes (seed automático "Asistente de contactos" en `/dolan_ai/agentes` + mensaje guía en la UI); (b) **sin ACL** `dolan.ai.agente` → AccessError para todos (ni admin). Fix: `security/ir.access.csv` (user r / system crud) + **SSE en step()** (el backend Codex exige `stream:true` SIEMPRE — también corregido en OCR) + loop con resultados previos en el prompt, read-timeout 90s, MAX_ITER 3.
3. **OCR no respondía**: `ocr.js` no cargaba (script faltante en la página) + mismo 400 stream:false. Fix: script incluido + SSE. **Verificado EN VIVO**: foto de factura generada → borrador `in_invoice` 808 con proveedor/líneas (luego limpieza); filtro de líneas sin precio (ruido de n° de comprobante).
4. **Entrada visible en Compras**: menú **"Escanear compra (IA)"** en Facturación y en Compras (dolan_dash), ancla `#ocr` que abre el selector de archivo.

**Verificación**: 32 tests DOLAN_ai (0 fallos); run en vivo del agente como juan → reply con nombres de contactos; OCR en vivo → borrador 808 (limpiado); menús visibles en secciones de Facturación; consola 0 errores.

### L30 — Selector de agentes + OCR con PDF (2026-10-28)

Verbatims: "el selector de agentes esta vacio y sigue sin funcionar", "las facturas para el OCR tienen que soportar PDF porque viene en pdf generalmente".

- **Selector vacío**: en el servidor el seed ya funcionaba (ruta `/dolan_ai/agentes` devolvía el agente; probe confirmado opts=1) — el browser del usuario tenía **JS cacheado viejo** (page.js/ocr.js sin el bloque de agentes) → **cache-bust `?v=30`** en ambos scripts + `no-store` ya presente. Verificado browser: select con "Asistente de contactos".
- **OCR con PDF** (dual-path en `ocr.py`):
  - PDF con imágenes/escaneado → **pypdfium2** (instalado en el contenedor, raster 2x, máx 3 páginas) → página 1 → visión (input_image).
  - PDF digital (texto embebido, típico ARCA) → **pdfminer extract_text** (≥60 chars) → modo texto (`input_text`, mismo prompt JSON) — más barato y sin visión.
  - Controller acepta `data:application/pdf;base64,` (hasta 8MB), UI `accept=".pdf,image/*"`.
  - Fallback con error claro `pdf_sin_soporte` si no rasteriza ni tiene texto.
- **Verificación**: PDF de prueba (imagen→PDF) en vivo → **borrador 810** creado con proveedor/líneas y limpiado; 36/36 tests; browser final selector+accept+0 errores (captura l30-ocr-pdf.png).
- Nota de infra: `pypdfium2` se instaló con `pip --break-system-packages` **dentro del contenedor** (se pierde si se recrea el contenedor) → pendiente: bake en Dockerfile (task técnica para próxima pasada de stack).
