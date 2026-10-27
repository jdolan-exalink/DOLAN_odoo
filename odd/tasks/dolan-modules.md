# Plan de desarrollo DOLAN_* — un módulo por dominio (Odoo 20 CE)

Estado: plan (F0 ejecutado; F1-F5 pendientes de aprobación/orden).
Política del proyecto: Odoo 20 **CE**, LGPL-3, sin modificar core, sin copiar
código Enterprise (OPL-1); parity solo por observación de comportamiento.
Docs base: `DOLAN_theme/docs/{ce-module-inventory,ce-coverage-matrix,ee-parity-facturacion,dolan-ai-design}.md`.

## Specs

- **S1** (verbatim): "quiero que activemos el trial de modulo de contabilidad, compras, AI, empleados, articulos, inventario, codigo de barra, flotilla, alquileres, subcripciones, calidad, mantenimiento"
- **S2** (verbatim): "la idea es que sean modulos DOLAN_contabilidad y asi por cada uno"
- **S3** (verbatim): "armemos un plan de desarrollemos tambien usando el MCP REA"
- **S4** (verbatim): "que tenemos listo y que falta?"
- **S5** (verbatim): "dale vamos en ese orden, los modulos que trae la CE quiero que verifiquemos los dashboard de modulos para quyue quede mas estetica enterprise"

## Estado (frente a S1): listo vs falta

| Dominio | Módulo pedido | En imagen CE | Estado en `dolan` (2026-10-27) | Qué falta |
|---|---|---|---|---|
| contabilidad | `account` | ✓ | installed (+`l10n_ar`, `l10n_ar_fiscal_ws`, `l10n_ar_ux`) | capa DOLAN_contabilidad (mejoras) |
| compras | `purchase` | ✓ | installed (+`l10n_ar_purchase`, CSV P3 validado) | capa DOLAN_compras (mejoras) |
| AI | — (no es app Odoo) | — | diseño `dolan-ai-design.md` | **construir `DOLAN_ai`** (decisión proveedor) |
| empleados | `hr` | ✓ (+24 módulos `hr_*`) | installed | capa DOLAN_empleados; familia holidays/recruitment después |
| artículos | `product` | ✓ | installed | capa DOLAN_articulos |
| inventario | `stock` | ✓ | installed (+`stock_account`, `l10n_ar_stock`) | capa DOLAN_inventario |
| código de barras | `barcodes` ✓ / `stock_barcode` = **uninstallable (EE)** | parcial | `barcodes` installed | **construir `DOLAN_codigo_barras`** (app de escaneo tipo EE sobre CE) |
| flotilla | `fleet` | ✓ | **installed (F0)** (+`fleet_maintenance`) | capa DOLAN_flotilla (costos, VTV/seguros) |
| alquileres | — | **NO existe en CE** | — | **construir `DOLAN_alquileres`** |
| suscripciones | `sale_subscription` = **uninstallable (EE)**; `mysubscription` = scaffold | parcial | scaffold installed | **construir `DOLAN_suscripciones`** |
| calidad | — | **NO existe en CE** | — | **construir `DOLAN_calidad`** (sobre `mrp` instalado) |
| mantenimiento | `maintenance` | ✓ | **installed (F0)** (+`hr_maintenance`, `fleet_maintenance`, `stock_maintenance`) | capa DOLAN_mantenimiento (mejoras) |

**Resumen**: 8 de 12 dominios ya corren hoy con apps CE nativas instaladas
(verificado por RPC/estado); **4 requieren módulo propio** (AI, código de
barras-completo, alquileres, suscripciones, calidad — 5 si se cuenta la app
de barcode) y 7 DOLAN_* son capas de mejora sobre lo nativo.

## Estrategia por módulo (S2: `DOLAN_<dominio>`)

Dos arquetipos:

- **A — Enhancer (base CE ya instalada)**: `DOLAN_contabilidad`, `DOLAN_compras`,
  `DOLAN_empleados`, `DOLAN_articulos`, `DOLAN_inventario`, `DOLAN_flotilla`,
  `DOLAN_mantenimiento`. Patrón ya probado con `dolan_dash`: herencias de
  vistas, dashboards KPI, flujos AR, sin tocar core; depende solo de la app base.
- **B — Módulo completo (el dominio no existe en CE)**: `DOLAN_ai`,
  `DOLAN_codigo_barras`, `DOLAN_alquileres`, `DOLAN_suscripciones`,
  `DOLAN_calidad`. Modelos + vistas + flujos propios, LGPL-3, dependencias
  mínimas (`account`, `stock`, `mrp` según corresponda).

| Módulo | Arquetipo | Base CE | Alcance v1 | REA por defecto |
|---|---|---|---|---|
| DOLAN_contabilidad | A | account + l10n_ar | dashboard contable (IVA, retenciones, cash-flow), accesos | parity panel EE |
| DOLAN_compras | A | purchase + l10n_ar_purchase | OC→remito→factura, plantilla CSV, alertas proveedor | parity panel Compras EE |
| DOLAN_empleados | A | hr | KPIs personal, timeline, integración con dolan_dash | parity app Empleados EE |
| DOLAN_articulos | A | product | listas de precio AR, campos extra, códigos | parity catálogo EE |
| DOLAN_inventario | A | stock + stock_account | UX remitos, alertas de stock, ajustes guiados | parity panel Inventario EE |
| DOLAN_flotilla | A | fleet | costos (combustible/service), VTV/seguros con alertas | parity Fleet EE |
| DOLAN_mantenimiento | A | maintenance | UI órdenes + KPIs, puentes hr/fleet/stock ya instalados | parity Maintenance EE |
| DOLAN_codigo_barras | B | barcodes (+gs1) | app de escaneo dedicada (recepción/ubicaciones) sin `stock_barcode` | parity Barcode EE |
| DOLAN_alquileres | B | account/stock | bienes, contratos, períodos, facturación, devolución | parity Rental EE |
| DOLAN_suscripciones | B | account/sale (si habilita) | planes, recurrencia, crons de facturación, escalonamiento | parity Subscriptions EE |
| DOLAN_calidad | B | mrp/stock | checklists, puntos de control, no conformidades | parity Quality EE |
| DOLAN_ai | B | account/purchase | `dolan-ai-design.md` (OCR compra F1, asistente F2) | n/a (diseño propio) |

## Uso del MCP REA (S3)

Estado: REA instalado (229 tools; WSAA verificado; Ghidra/JDK seteados).

- **R1 — Conectividad**: REA se adjunta a un Chromium controlado por nosotros
  con **CDP** (`--remote-debugging-port`) para observación de páginas; la demo
  EE (exalink) se abre con Playwright (ya probado) y las credenciales solo en
  env/tmpfs. `discover_webmcp_tools` de REA sigue documentado como incompatible
  con el SaaS Odoo *plain* (hallazgo L de la fase de estudio EE).
- **R2 — Parity por dominio**: para cada fila de la tabla anterior, capturar
  con REA/Playwright el **comportamiento** EE (flujos, campos, botones,
  mensajes) → `docs/ee-parity/<dominio>.md` → alimenta `ce-coverage-matrix.md`.
  **Límite duro**: solo observación; prohibido copiar/extraer código EE (OPL-1).
  REA en modos de binario/artefacto se usa para análisis propios (p. ej.
  estructura de la imagen Odoo), nunca de artefactos Enterprise.
- **R3 — Aceptación**: cada DOLAN_* se acepta contra su spec de parity +
  verificación Playwright local (lista/form + claro/oscuro + rol no-admin),
  igual que los lotes ya entregados de DOLAN_theme.

## Fases (orden propuesto)

| Fase | Contenido | Estado |
|---|---|---|
| **F0** | Activación: `fleet`, `maintenance` + puentes `*_maintenance` instalados en `dolan` (estado verificado, RPC auth uid=7, 0 errores post-deploy); resto de apps pedidas ya estaba installed | ✅ 2026-10-27 |
| **F1** | REA/parity de los 12 dominios (3 lotes: núcleo cont/compras/artículos/inventario → rrhh/flotilla/mantenimiento → EE-only alquileres/suscripciones/calidad/barcode/AI) | ⬜ |
| **F2** | Enhancers arquetipo A: quick wins sobre lo ya instalado (DOLAN_mantenimiento, DOLAN_flotilla, DOLAN_contabilidad) | ⬜ |
| **F3** | Módulos completos arquetipo B: DOLAN_codigo_barras, DOLAN_alquileres, DOLAN_suscripciones, DOLAN_calidad | ⬜ |
| **F4** | DOLAN_ai: requiere decisión explícita (proveedor cloud sí/no, presupuesto tokens, local vs cloud para OCR) | ⬜ (bloqueado decisión) |
| **F5** | Integración: home por rol, accesos, e2e completo, cobertura de la matriz sin `NE` | ⬜ |

Cada fase entra al flujo ODD normal (tareas por slice ≈400 líneas, tests,
verificación en browser, commit por unidad de trabajo).

## Riesgos

- **AI (ítem 2)**: credenciales de proveedor → solo env/secrets (regla ya
  vigente para certs/WSAA); cuotas y log de uso; default local (Ollama).
- **Suscripciones/alquileres (ítem 1/3)**: modelos propios de facturación
  recurrente tocan dinero → tests primero (crons, montos, ARCA).
- **barcode (ítem 6)**: si `barcodes` CE no cubre el flujo, el módulo propio
  debe cubrirlo con tests E2E de escaneo.

## Log

- **L1** (verbatim, 2026-10-27): "que tenemos listo y que falta? quiero que activemos el trial de modulo de contabilidad, compras, AI, empleados, articulos, inventario, codigo de barra, flotilla, alquileres, subcripciones, calidad, mantenimiento y armemos un plan de desarrollemos tambien usando el MCP REA, la idea es sque sean modulos DOLAN_contabilidad y asi por cada uno"
- **L3** (S5, 2026-10-27): orden aprobado F1→F2→F3 y pedido inmediato: verificar los dashboards de los módulos CE y llevar su estética a nivel Enterprise. Capturas actuales en `DOLAN_theme/qa/shots/dash/` (contabilidad, inventario, compras, empleados, mantenimiento, productos, apps-grid); gaps: chips de navbar rellenos violeta vs barra clara EE, franja KPI gris de Compras, tarjetas del Resumen de inventario planas con títulos EN y barras grises (¿skeleton?), rail con solo 14 apps en DOM (falta Flotilla/Punto de venta/Manufactura vs 34 en grid), captura de Flotilla cayó en el grid, píldora de Mantenimiento sin acento. Referencia EE: `docs/evidence/ee-demo/01-dashboard-facturacion.png`.
- **L2** (evidencia F0): imagen odoo:20.0 auditeada: `fleet`/`maintenance` instalados con puentes `fleet_maintenance`/`hr_maintenance`/`stock_maintenance` (auto_install) en `dolan`; UI 200; auth RPC uid=7; 0 errores de log post-20:31:09; blip transitorio de registry durante la carga (query de `ir_model_fields` en ventana de migración) resuelto solo al reload (source = core `base/ir_model.py`, query OK después); apps pedidas = installed: account, purchase, product, stock, barcodes, hr, fleet, maintenance, mrp. `stock_barcode` y `sale_subscription` = uninstallable (EE); `quality` y rental no existen en la imagen; `mysubscription` = scaffold LGPL-3 ya instalado.

### L18 — S5: estética Enterprise en dashboards CE (2026-10-27)

**Ejecutado (F2 rápido sobre apps CE nativas):**
- Capturas previas de 8 vistas (`DOLAN_theme/qa/shots/dash/`: contabilidad, inventario, compras, empleados, mantenimiento, productos, apps-grid, flotilla→grid) vs referencias EE (`docs/evidence/ee-demo/01-dashboard-facturacion.png`).
- **Navbar**: core Odoo 20 pinta chips `rgb(113,99,158)` — overrides en `navigation.scss`: `.o_nav_entry` **y** `.o-dropdown.dropdown-toggle` (secciones, company switcher, usuario) → fondo transparente, texto token, hover/abierto `pri-soft`. Verificado por probe: `bg rgba(0,0,0,0)` en ambos.
- **Compras**: `.o_purchase_dashboard .purchase-dashboard-card` (incl. variante `bg-dark-subtle` de conteo 0) → tarjetas blancas con borde/radio/sombra, número `fs-2` bold, hover con acento. Capturas `s5b-compras.png`.
- **Inventario**: `.o_card_record` (tarjetas card-record Odoo 20) → superficie, borde, radio, sombra; títulos y `Abrir` con tokens. Capturas `s5b-inventario*.png`.
- **Badges/pills** kanban → radio 999px + peso 700.
- **Oscuro real**: param `dolan.ui.tema=oscuro` (ORM `set_str`) → probe `tema=dark` + capturas `s5b-{compras,inventario,mantenimiento}-dark.png` (0 errores de consola); **restaurado a `claro`** al final. `theme_apply.js` re-aplica config en `ACTION_MANAGER:UPDATE` (por eso inyectar el atributo a mano no sirve).

**NO cerrado (hallazgos con evidencia):**
1. **Rail 14/34**: `load_menus` como juan EXCLUYE fleet(456)/mrp(373)/pos(393) del payload pese a que `_filter_visible_menus` los conserva y no hay grupos ni blacklist → descarte interno de `load_menus` sin causa identificada (la rejilla de Aplicaciones sí los muestra porque usa otra vía). Postergado a investigación focalizada (candidato F1/REA).
2. Títulos EN del Resumen de inventario (Receipts…) = términos core sin traducir → no se toca core; documentado.
3. Barras grises = canvas Chart.js con colores core (no estilable por CSS limpio).
4. Artefacto visual en oscuro: caja negra arriba-izquierda del navbar (nuevo/visible solo en dark) → pendiente.
5. Filas fantasma de demo (Compras/Empleados) coexistiendo con empty-state → tema de datos, no de estilo.
6. Durante `-u` imprime `DOLAN_theme:8: Undefined substitution referenced: "---"` a stdout: **no bloqueante** (0 apariciones en odoo.log, `sass.compile` de los3 scss OK, runtime sirve los estilos, 0 errores de consola) — origen no identificado, ver en F1.
7. Delegación a `gentle-ai-worker` falló (2 veces: Required heading y error del asistente) → ejecución inline (fallback de la sesión).

**Veredicto S5**: estética Enterprise aplicada y verificada en claro y oscuro (capturas `s5b-*`). Risk: none (solo SCSS propio, cambios pedidos en S5; verificación Playwright probe+capturas claro/oscuro+consola en 0).
