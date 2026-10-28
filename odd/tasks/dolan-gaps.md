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

### L31 — Fix OCR UserError + rail universal + análisis IA EE (2026-10-28)

Verbatims: "cuando le di crear borrador tiro error Error creando: UserError", "quiero que analices bien como esta implementara la IA en el demo y implementemos simimlar", "la sidebar se rompe… en alquileres subscripciones, verifica todas las apps que funcione correctamente".

- **OCR UserError**: causa = fecha OCR sin formato ISO (p.ej. `25/10/2026`) cruda a `invoice_date` → `_norm_date` (ISO + dd/mm/yyyy + dd-mm-yyyy), total `$1.234,56`-safe, partner saneado; el controller ahora devuelve **detalle** del UserError al front (mensajes seguros, sin secretos) y ocr.js lo muestra. Tests: `_norm_date` + create **como usuario normal** (no shell root).
- **Rail universal**: nuevo `DOLAN_ai/static/src/js/embed_rail.js` compartido (CSS claro/oscuro + active route + load_menus) incluido en las **7 páginas** /dolan_* (ai, mantenimiento, flotilla, contabilidad, alquileres, suscripciones, código de barras). Bug de deploy detectado en el camino: `cp -r src/controllers dest/controllers` anidaba `controllers/controllers` y el stack servía main.py viejo → copia plana de archivos (regla nueva para deploys). Verificado: **7/7 páginas con rail 415 items + contenido, 0 errores** (capturas l31-*.png).
- **IA EE analizada** (nuevas capturas `ia-agentes-grid.png`, `ia-agente-form.png`): EE = agentes con chat tipo Discuss + historial, pestañas **Instrucciones/Habilidades/Artículos/Activadores**, tool-loop sobre "available tools". Spec de paridad en `ee-parity/ia-implementacion.md` con plan v2 (conversaciones persistentes multi-turno, instrucciones editables, más tools con caps, activadores post).
- Risk: item 2 sin cambios (same allowlist/caps; el detalle de error mostrado es mensaje de UserError sin secretos); item 3 sin cambios.

### L32 — Rail embebido real + fix cruce de empresas del OCR (2026-10-28)

Verbatims: "alquileres, subscripcions y dolan ia muestran una sidebar sin iconos y con nombres duplicados y en ingles", "Error creando: ¡Uy! Hay inconsistencias en la empresa: Borrador… DOLAN SS mientras que Contacto (partner_id: 'CINTIA VERONICA GOROSITO') pertenece a otra empresa".

- **Rail v32**: la fuente anterior (`load_menus` por call_kw) devolvía el árbol **interno** (jsonb crudo, sin `appID`/`webIconData`, con duplicados por submenús) → ahora usa **`GET /web/webclient/load_menus`** (forma JS del webclient: 40 apps con `appID==id`, nombres localizados es_AR, `webIconData`/`webIcon` con fallback de ícono oi, orden del `root.children`, highlight por ruta). Verificado browser en 4 páginas: **40 items, 40 con icono, 0 duplicados, 0 strings en_US** (capturas l32-*.png).
- **Cruce de empresas del OCR**: el borrador se creaba en la **compañía activa del usuario** (DOLAN SS) con un partner de otra (CINTIA VERONICA GOROSITO, company 7) → UserError de consistencia. Fix en `create_draft`: buscar partner (todas las compañías, `order company_id,id`) y crear el move con **`company_id = partner.company_id`** (el asiento vive en la entidad que compra, como debe ser en multi-compañía); partner **nuevo = compartido** (company_id False) para que no cruce nunca. Tests: partner de otra compañía con diario real (migra) + partner nuevo compartido.
- **Verificación en vivo del caso EXACTO del usuario** (como juan, activa DOLAN SS, partner GOROSITO): `{'ok': True, 'company': 'CINTIA VERONICA GOROSITO'}` → borrador draft en la compañía 7, luego limpieza total.
- Risk: item 3 sin cambios (multi-compañía ahora explícita y probada; ningún post, todo draft).

### L33 — IA v2 (paridad EE: chat con historial + instrucciones) (2026-10-28)

Según `ee-parity/ia-implementacion.md`:
- **Conversaciones persistentes**: `dolan.ai.conversacion` + `dolan.ai.mensaje` (roles user/assistant/tool, ACL user r/system crud) — cada turno queda guardado; el loop carga los últimos 12 como contexto (system = instrucciones del agente, user, **assistant con `output_text`** — contrato Responses API verificado empíricamente: assistant+input_text = 400).
- **Instrucciones editables**: `proposito` renombrado a **Instrucciones** (system-prompt del agente, inyectado como primer turno "system" — el backend lo acepta 200).
- **Más herramientas** (todas con caps): `search_count`, `read` (por ids), y `write` con **allowlist de campos por modelo** (res.partner: name/email/phone/mobile/street/city/comment/ref; crm.lead; project.project) — rechazo explícito `campos_no_permitidos`; unlink siempre prohibido.
- **UI tipo Discuss**: selector de agente + selector de conversación + hilo con burbujas por rol (Vos/Agente/🔧 herramienta) + composer; nueva conversación automática al primer mensaje.
- **En vivo (2 turnos)**: turno1 ejecuta search_read y responde *"Los dos contactos se llaman A TODO COLOR SRL."*; turno2 **recuerda el contexto** y aplica las instrucciones: *"No puedo contar los productos porque solo tengo acceso a contactos."* — exactamente el comportamiento "explain the limitation and offer closest next step" del EE.
- 52/52 tests DOLAN_ai. Risk: item 2 sin cambios (write limitado a campos blancos; sin unlink; caps; log en conversación).

**Verificación final L33**: 52/52 tests; en vivo 2 turnos con commit — turno1 *"Los 2 contactos se llaman A TODO COLOR SRL."* (con search_read ejecutada), turno2 *"Solo puedo buscar y contar contactos; no tengo acceso a los productos."* (recuerda contexto y limitación); browser muestra las 8 burbujas del hilo (Vos/Agente/🔧) con 0 errores (captura l33-chat-final.png). Nota: el shell de Odoo no commitea solo — cualquier prueba con persistencia necesita `env.cr.commit()` explícito.
