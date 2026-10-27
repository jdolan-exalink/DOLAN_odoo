# DOLAN_theme — Fase 0: Investigación (auditoría técnica)

**Fecha**: 2026-10-27 · **Estado**: auditoría de entorno completada sobre evidencia verificada; sin programación del tema.

## 1. Entorno Odoo verificado

| Dato | Valor verificado | Cómo |
|---|---|---|
| Versión | **20.0-20261015 (final)** | `odoo.release.version` dentro del contenedor |
| Imagen | `odoo:20.0` (Docker Hub oficial) | `Dockerfile FROM odoo:20.0` del stack |
| Commit | no expuesto por el paquete (`odoo.release.git = n/a`) | El pin reproducible usable es **tag `odoo:20.0` + release `20.0-20261015`** |
| Edición | Community (núcleo) | addons del core: 693 manifests, **34 aplicaciones, todas LGPL-3** |
| Base de datos | PostgreSQL 17 (docker `postgres:17`) | stack `odoo20-argentina` |
| Stack | Docker Compose funcional en `10.1.1.34:8070` | ya usado en producción interna (DB `dolan`) |
| git / Playwright | git 2.47.3 ✓ · **Playwright NO instalado** (bloqueo de tooling para QA browser, ver riesgos) | chequeo directo |

> El pin de versiones se fija por **tag de imagen + versión de release**; no hay artefacto de commit oficial dentro de la imagen publicada.

## 2. Arquitectura frontend de Odoo 20 (evidencia propia del entorno)

Verificado en vivo durante esta sesión (2026-10-26/27), no supuesto de documentación:

- **OWL 3**: el runtime de componentes es Owl 3 con reglas duras (ver `odoo20-compatibility.md`).
- **Assets**: boot en `web.assets_web.*` (JS ~8,3 MB + CSS); bundles diferidos tipo `web.assets_backend_lazy`; endpoint **`GET /web/bundle/<nombre>`** devuelve la lista de URLs con hash para un bundle; los hashes cambian al recompilar (`-u`).
- **Vistas**: el tipo `tree` **ya no existe** → `list` (error real: `View types not defined tree`). Existen tipos `pivot` y `graph` con vistas default para `account.move` y `stock.picking`.
- **Controllers** (jsonrpc): `/web/action/load` (enteros o xmlid con punto), `/web/dataset/call_kw` (si el registry corriendo no tiene el modelo → `NotFound`; **el proceso vivo necesita restart tras `-u` que agrega modelos**), `/web/session/authenticate`.
- **Campos jsonb**: `ir_ui_view.arch_db`, `ir_act_window.name`, `ir_act_window.domain` (consultas SQL deben usar `name->>'en_US'`).
- **board.board**: sin registros por XML; el widget `parseInt(node name)` exige ids **numéricos** en `<action name>` → en XML de datos usar `%(xmlid)d`.
- **Menús**: `ir.ui.menu.action` devuelve **recordset** (no string) al leerlo desde ORM.
- **Traducciones**: sin `ir_translation` (tabla inexistente); traducciones live desde `i18n/*.po` con fallback de idioma raíz (`es_AR` → `es`).

## 3. Diferencias Odoo 19 → 20 detectadas (no asumir compatibilidad)

| Área | Odoo 19 (supuesto viejo) | Odoo 20 (verificado) |
|---|---|---|
| Client JS | Owl 2: `static props`, `useState`, `state.x` pelado en templates | Owl 3: **sin** `static props` (useProps si hay schema), **sin `useState`** → `this.state = proxy({..})` (import de `@odoo/owl`), templates con **`this.state.x` explícito**, `t-out` (no `t-esc`) |
| Vistas | `view_mode` con `tree` | `list` |
| config params | `get_param/set_param` | **tipado**: `get_str/set_str/get_int/set_int/...` |
| res.users | `groups_id` | `group_ids` |
| Wizard contraseña | `change.password.wizard.new_password` | sin campo; usar `user._change_password()` |
| res.company imagen | `image_1920` | `logo` / `logo_web`; binarios aceptan base64-str o `BinaryValue` |
| res.lang | tabla `res.lang` | tabla **`res_lang`** |
| account.account | `company_id` | sin columna company (códigos por compañía en `code_store` JSON) |
| stock.move | `name`, `action_done()` | `description_picking(_manual)`, `_action_done()` |
| warehouse | auto-crea por company | solo company default (`create_missing_warehouse` es de primer arranque) |
| Módulos 19.x | instalables con bump de versión | `check_version` por serie **fuerza `installable=False`** con version 19.x en serie 20 (bump manual NO valida el código, ver riesgos) |
| ir.config_parameter lookup | — | ver fila "config params" |

**Evidencia dura de incompatibilidad cross-version**: `web_responsive` (OCA, rama 19.0) instalado con versión bumpeada **rompió toda la UI** (pantalla blanca): `AppsMenu` con `static props` en Owl 3 + patch de chatter dependiente de `@mail/chatter/web_portal/chatter` (reestructurado) + extensión de `web.ListView.EditableButtons` (inexistente). Lección: **las validaciones server-side no prueban JS/Owl; solo el navegador**.

## 4. Estado de addons OCA de interfaz para Odoo 20

Verificado con `git ls-remote`/`ls-tree` de `github.com/OCA/web`:

| Rama | Contenido |
|---|---|
| `20.0` | **`web_responsive` NO existe** (solo migran a la rama nueva lo migrado); únicos de interfaz: `web_environment_ribbon`, `web_m2x_options` |
| `19.0` | `web_responsive` existe (19.0.1.1.1, LGPL-3, deps `web,web_tour,mail`) — **probado y rechazado**: rompe Owl 3 (arriba) |

Decisión registrada: **no instalar addons de 19.0 a ciegas**; DOLAN_theme implementa su propia navegación/estética sobre puntos de extensión oficiales.

## 5. Patrones UX Enterprise (referencia documental, sin código propietario)

Fuentes autorizadas (docs/demos públicas de Odoo): home con grid de apps; barra superior con menú de apps + buscador global + breadcrumbs de control panel; formularios con estado/acción principal arriba (botón Guardar/Validar primario), grupos colapsables, pestañas; listas con barra de búsqueda con filtros/guardados y panel de búsqueda; densidades y modo oscuro; Kanban con estados. **No se extrajo ni copiará código de Enterprise** (OPL-1): se replican patrones funcionales con implementación propia LGPL.

## 6. REA / Playwright

- REA (MCP) disponible en esta sesión y autorizado para artefactos; para UI web **el navegador manda** (regla ya aprendida aquí: 6 rondas de errores solo visibles en browser). Playwright **no está instalado** → requerido para automatizar la fase de QA/prototipos (pendiente de instalar con aprobación; bloqueo documentado en `risks.md`).
- Plan: Playwright contra el stack de dev (nunca contra `dolan` de producción) para capturas y regresiones.

## 7. Riesgos por vertical detectados en el stack real

Instaladas en la DB actual (contexto de prueba): `sale_management, purchase, stock, account, mrp, point_of_sale, project, crm, hr, hr_expense` + verticales AR propias (`l10n_ar*`). Riesgos concretos en `risks.md` (POS táctil, editor Website, facturación latam, chatter).

## 8. Método y decisiones

1. Evidencia > supuestos (cada hecho con verificación).
2. El navegador es el juez final del frontend; los bundles compilados solo prueban sintaxis.
3. Sin dependencias de OEEL-1; sin editar core; sin frontend paralelo.
4. Nombre de addon: `DOLAN_theme` **validado** contra `MODULE_NAME_RE = ^\w{1,256}$` de Odoo 20 (regex acepta mayúsculas; convención OCA es minúsculas — se documenta, no se renombra sin aprobación).

## 9. Entregables de esta fase

`docs/research.md` (este) · `docs/architecture.md` · `docs/odoo20-compatibility.md` · `docs/risks.md` · semillas: `docs/ce-module-inventory.md`, `docs/ce-coverage-matrix.md`, `docs/version-support-policy.md` · prototipos en `docs/prototypes/`.
