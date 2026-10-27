# DOLAN_theme — Compatibilidad con Odoo 20 (matriz de soporte)

**Objetivo**: única fuente de verdad sobre qué versión soporta qué y con qué evidencia.

## 1. Identidad del addon

| Check | Resultado | Evidencia |
|---|---|---|
| Identificador exacto solicitado | `DOLAN_theme` | mandate del usuario |
| Regex de Odoo 20 para nombres de módulo | `MODULE_NAME_RE = ^\w{1,256}$` (`modules/module.py:56`) | **VÁLIDO**: `\w` incluye mayúsculas |
| Convención OCA/Habilitación | minúsculas y `_` (estilo `dolan_theme`) | convención, no restricción del runtime |
| Decisión | **Usar `DOLAN_theme` tal cual** (renombre requiere aprobación explícita) | mandate: "No sustituir el nombre sin aprobación" |

## 2. Matriz versión → estado (política completa en `version-support-policy.md`)

| Odoo | Estado DOLAN_theme | Notas |
|---|---|---|
| 20.0-20261015 (CE, imagen `odoo:20.0`) | **Objetivo certificado v1** | Única versión verificada en el entorno |
| 19.x | **No soportado** | Sin migración silenciosa; no se instalan addons 19 (evidencia: `web_responsive` rompe UI) |
| 21.x | No disponible → no prometido | Diseño con capas `compat` preparadas; certificar al existir |

## 3. Checklist Owl 3 / client-side de Odoo 20 (obligatorio en todo JS del tema)

Reglas probadas en navegador en esta sesión (5 fallos reales):

1. **Sin `static props`** en componentes (si hace falta schema: `useProps`).
2. Estado reactivo: **`this.state = proxy({...})`** con `proxy` importado de `@odoo/owl` (no `useState` — no existe).
3. Templates: **`this.state.x` / `this.campo` explícito** — los identificadores pelados NO resuelven campos del componente (solo props).
4. **`t-out`**, nunca `t-esc` (deprecado; emite warning en compile).
5. Imports verificados contra core: `rpc` (`@web/core/network/rpc`), `useService` (`@web/core/utils/hooks`), `registry` (`@web/core/registry`).
6. En vistas board: `name` numérico (`%(xmlid)d` en data XML).
7. `view_mode` sin `tree` (usar `list`).
8. Tras `-u` que agrega modelos, **reiniciar el proceso** (workers=0 conserva registry viejo).
9. Dominios guardados: **nunca `ref()`** (se persiste sin resolver; el JS del cliente no lo evalúa).
10. Los assets que corre el navegador pueden estar en `web.assets_web` (no solo `assets_backend`): verificar el bundle que carga el browser (`/web/bundle/<nombre>` → URLs con hash).

## 4. Puntos de extensión oficiales usados (confirmados en 20)

- `ir.ui.view` inherit (form/list/kanban/search/board) — data XML.
- Assets por manifest (`web.assets_backend`, `web.assets_web` con cuidado): SCSS/JS/XML de templates OWL.
- `registry.category("actions" | "services" | ...)` — registro de client actions y servicios.
- Menús: `ir.ui.menu` (sequence = orden → base del App Launcher) + `ir.model.data`.
- `ir.config_parameter` (API tipada) para preferencias globales; `ir.default` para defaults por modelo/empresa.
- Preferencias por usuario: campos en `res.users`/`ir.default` (respetando ACL).

## 5. OCA / terceros para interfaz (Odoo 20)

| Addon | Rama 20.0 | Acción DOLAN_theme |
|---|---|---|
| `web_responsive` | **ausente** | no instalar (19.0 probado = pantalla blanca Owl3) |
| `web_environment_ribbon` | presente | no requerido; evaluar en Fase 5 si aporta |
| `web_m2x_options` | presente | no requerido; evaluar después |
| Otros `web_*` OCA | revisar rama 20.0 addon por addon antes de usar | regla: si no está en 20.0, no se usa |

## 6. Reglas de conservación (no negociables)

- No modificar core; heredar vistas/assets/registries.
- Preservar permisos, ACL, record rules, multiempresa y validaciones (el tema no toca lógica de negocio; **nunca ocultar campos como medida de seguridad**).
- Sin código OEEL-1/Enterprise; patrones visuales replicados en código propio LGPL-3.
- POS: estilos aislados (ver `risks.md`); Website/editor: sin inyecciones globales invasivas.
