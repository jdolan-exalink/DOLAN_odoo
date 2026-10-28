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

### L4 — Monorepo DOLAN_odoo (2026-10-27)

- **L4a** (verbatim): "vamos a renombrar a DOLAN_odoo20 y adentro vamos a tenerr los distintos modulos dentro de ellos vamos a tener un DOLAN_theme, DOLAN_ai, DOLAN_XX, creemos el monorepo yo mientras voy a ir logeando y creando la carpeta de github"
- **L4b** (verbatim): "te dejo el repo y ya estas logueado https://github.com/jdolan-exalink/DOLAN_odoo.git"
- **Ejecutado**: rename `/root/odoo20` → `/root/DOLAN_odoo20` (+ symlink de resguardo `/root/odoo20`, compatibles todos los paths de docs/scripts); stack sano post-rename (UI200, containers Up, compose desde la nueva ruta OK). Monorepo: `DOLAN_theme/.git` absorbido (0 commits), fuentes `dolan_dash`/`dolan_ui` copiadas a la raíz (deploy en `odoo20-argentina/addons/` intacto), `.gitignore` (runtime/datos/backups/secrets/repos anidados ignorados; `compras_plantilla.csv` forzado a trackear), README con tabla de estructura + URL. Historial inicial `main` (7 commits, mensajes conventional EN): `fc722d4` scaffold → `7be3aa9` DOLAN_theme → `610346c` docs/qa → `27fa261` DOLAN_ai → `d18c0db` dolan_dash/dolan_ui → `fdea4e7` stack → `4cdf78a` odd. **Push a `origin/main` OK** (auth `gh` como jdolan-exalink). Ignorados con historia propia: `bak/.git` (commits WSFE previos) y `odoo20-argentina/addons/.git` (dubious ownership) — documentados, no absorbidos. Próximos módulos = carpetas `DOLAN_XX/` siguiendo la convención.

### L19 — S5 cierre: estética completa de lo analizado hoy (2026-10-27)

Los 6 gaps abiertos en L18 quedaron CERRADOS con verificación:

1. **Rail 14→18 apps**: causa raíz = las raíces de `fleet`/`mrp`/`point_of_sale` tenían `group_ids` de app (Encargado de vehículos, mrp Usuario/Administrador, pos Usuario/Administrador) que `juan` no tenía → `_visible_menu_ids` las excluía del payload de `load_menus` (no era un bug de plantilla ni del rail). Fix = **grants** de esos grupos a juan (ORM, sin tocar datos core). Verificado: rail con `fleet.menu_root`, `mrp.menu_mrp_root`, `point_of_sale.menu_point_root` + `DOLAN_ai` (18 items, capturas s6-*).
2. **Títulos EN del Resumen de inventario**: 14 `stock.picking.type` sin traducción `es_AR` → escritos términos oficiales (Recepciones / Órdenes de entrega / Fabricación / Pedidos de PdV). Verificado en browser: `["Recepciones","Órdenes de entrega","Fabricación","Pedidos de PdV"]`.
3. **Caja negra oscura (navbar)**: `navigation.scss` estilizaba `.o_navbar_apps_menu` como panel dropdown (bg/border/min-width 460) pero en Odoo20 esa clase = contenedor del **botón** en la topbar → neutralizada el wrapper + el panel real (`o_dropdown_menu`) estilizado con tokens. Verificado: probe `boxBg=transparent` + `s6-navbar-dark.png` sin artefacto.
4. **Filas fantasma**: son el *sample data* nativo de Odoo (`useSampleModel`) — SCSS propio `.o_view_sample_data` a `opacity .04` en filas de lista y kanban. Verificado: `n=10, op=0.04`.
5. **Error `-u`: `DOLAN_theme:8: Undefined substitution "---"`**: origen = los `README.md`/`docs/*.md` del addon (copiados al stack) parseados como **RST** por el fallback docutils cuando `markdown2` no está instalado → eliminados `docs/` y `README.md` de las copias stack (la fuente vive en el monorepo). `-u` posterior **limpio** (0 apariciones).
6. Consola 0 errores en todas las capturas; tema restaurado a `claro`.

Evidence: `DOLAN_theme/qa/shots/s6-{inventario,compras,navbar-dark}.png`.
Risk: none (grants = otorgar al propio admin grupos de apps instaladas; traducciones = datos es_AR añadidos; SCSS propio; verificación browser+probe en claro/oscuro).

### L20 — Aprobación F2 + F3 (2026-10-27)

- **L20** (verbatim): "vamos con F2 y F3"
- Alcance = tabla de estrategia del plan (S2): F2 enhancers `DOLAN_mantenimiento`, `DOLAN_flotilla`, `DOLAN_contabilidad`; F3 completos `DOLAN_codigo_barras`, `DOLAN_alquileres`, `DOLAN_suscripciones`, `DOLAN_calidad`. Patrón: addon propio en el monorepo + deploy a `odoo20-argentina/addons/`, página/kpi por controller (patrón DOLAN_ai), tests TransactionCase, un commit por módulo, sin core modificado.

### L21 — F2 + F3 ejecutadas (2026-10-28)

Veredicto: **7 módulos entregados**, todos instalados en `dolan` con tests GREEN y verificación browser (consola 0 errores), un commit por módulo (pushed a origin/main).

**F2 enhancers (A)** — páginas KPI con controller propio (patrón DOLAN_ai) + menú dentro de la app existente:
| Módulo | Alcance v1 | Tests | Evidencia browser |
|---|---|---|---|
| `DOLAN_mantenimiento` | OT abiertas/críticas/atrasadas/próximas 7d + equipos | 3 ✓ (schedule_date) | `/dolan_mantenimiento` 200, cards |
| `DOLAN_flotilla` | contratos 30d/vencidos + costos mes (services/contracts) | 3 ✓ | `/dolan_flotilla` 200, cards |
| `DOLAN_contabilidad` | emitidas/recibidas + IVA débito/crédito/liquidado del mes | 4 ✓ (datos reales: IVA déb 1.95M / créd 1.04M) | `/dolan_contabilidad` 200 |

**F3 completos (B)** — apps con raíz+icono:
| Módulo | Alcance v1 | Tests | Verificación |
|---|---|---|---|
| `DOLAN_codigo_barras` | escaneo SKU/barras → producto + existencias por ubicación (página con autofocus) | 2 ✓ | scan real `PRD-001` → card "Articulo Demo General 21%" |
| `DOLAN_alquileres` | contratos por día: importes, estados, botón Facturar → `account.move` draft | 5 ✓ | rail + app instalada |
| `DOLAN_suscripciones` | planes + suscripciones + **cron diario** que genera facturas draft y avanza períodos | 5 ✓ | rail + cron registrado |
| `DOLAN_calidad` | puntos de control, controles OK/KO (KO crea no conformidad), cierre con solución | 5 ✓ | rail + app instalada |

**Rail**: 18 → **21 apps** (Alquileres, Suscripciones, Calidad con iconos propios PIL).

**Odoo 20 rename-gauntlet de esta tanda** (todos verificados empíricamente):
`ir.model.access` → **`ir.access`** con CSV `security/ir.access.csv` y columnas **`model_id/id,group_id/id,operation,domain`** (sin perm_read/write/...); **ACL importan para menús**: un menú hijo cuyo modelo sin `ir.model.access` desaparece del `load_menus` (raíces nuevas invisibles); `Environment` v20 **no tiene `.sudo()`/`.with_context()`** (sudo en recordsets); `product.template.type='product'` → **`consu` + `is_storable`**; `ir.cron.numbercall/doall` eliminados; `maintenance.request.date_planned_finished` → **`schedule_date`**; `fleet.vehicle.log.contract`: `start_date`/`expiration_date`/`amount` y **no existen `log.fuel` ni `log.odometer`**; `account.move.parent_state` → `state` (aml: `move_id.state`); `product.template.default_code` con variante archivada → `active_test=False`.

Risk: item 3 (contratos de datos: modelos/menús propios; ACL otorgadas a group_user/system) — verificación: 22 tests verdes + browser rail/scan/páginas; item 1 sin cambios (facturas/cron solo crean borradores; ninguna acción postear).

### L22 — Activación total + análisis con REA + demo EE abierta (2026-10-28)

- **L22a** (verbatim): "vamoos con RAE y quiero que actives y analices todos los modulos"
- **L22b** (verbatim): "te active todos los modulos enterprise en la demo para que los veas"
- Ejecutado: REA R1 (CDP propio :9222, inspect ev_996edf…, sesión 40s/10 apps ev_fd320c… timeline88 drops0); activación **38/38 apps CE** en4 lotes (UI200 c/u); barrido Playwright **38/38** (200 OK, 2 errores consola hr/hr_recruitment TypeError 'type', capturas en qa/shots/analysis/); remedios: grants de10 grupos de raíz + fix hr_holidays (acción derivable + ACL) → **rail 38/38**; demo EE: grilla26 tiles +8 capturas EE-only/en-paridad (suscripciones, alquiler, IA/agentes, taller, código-de-barras, manufactura, ventas, contabilidad) en docs/evidence/ee-demo/full/. Doc completo: `DOLAN_theme/docs/modulos-analisis.md`. Nuevos gaps: **Taller (field service) sin equivalente CE**; EE IA=Agentes vs nuestro DOLAN_ai ChatGPT-only. Risk: none (activación en DB test con backups; grants = permisos al propio admin; datos propios; verificación por lote + barrido completo).

### L23 — F1: specs de parity EE→nuestros (2026-10-28)

- **L23** (verbatim): "vamos con F1 primero una vez terminados todos los modulos podes arrancar el F5 y luego desarrollar todo lo que falta"
- Orden comprometido: **F1 → (módulos a paridad) → F5 → resto de gaps (DOLAN_taller, v2 de subs/alquiler/barras, Declaración fiscal, IA-agentes)**.
- Entregado: 6 specs en `DOLAN_theme/docs/ee-parity/` (suscripciones, alquileres, codigo-barras, contabilidad, ia, taller) a partir de las capturas EE de L22 + tabla F1 en `ce-coverage-matrix.md`.
- Hallazgo clave: **`mrp_workorder`, `mrp_plm`, `stock_barcode` = uninstallable** en esta build CE → "Taller" EE no tiene equivalente nativo → confirmado gap `DOLAN_taller` (post-F5); `DOLAN_calidad` queda como capa de control de calidad sobre operaciones.
- Risk: none (sólo docs/evidencia; sin cambios de código ni datos).

### L24 — v2 de los tres módulos a parity F1 (2026-10-28)

Orden comprometido en L23 ejecutado para Suscripciones/Alquileres/Código de barras:

- **DOLAN_alquileres v2**: `fecha_pickup`/`fecha_return` (datetime), `estado_ops` (Por retirar/Recolectada/Devuelta) con badge en lista, `estado_factura` (Sin facturar/Por facturar/Facturado) con `@api.depends(move_id.state)`, **página KPI tipo EE** `/dolan_alquileres` (Hoy·Pickups·Returns·Tarde·Por confirmar·Por facturar) + menú Tablero. Tests deltas (9 ✓).
- **DOLAN_suscripciones v2**: `user_id` (Vendedor, avatar en lista), `fase` (Cotización/Renovado/Venta adicional), `proxima` **stored** → vistas **calendar + graph** en la acción, **página MRR** `/dolan_suscripciones` (MRR normalizado30d, activas, próx.7d, por facturar, planes) + menú Tablero MRR. Tests deltas (10 ✓).
- **DOLAN_codigo_barras v2**: resolución en cadena **producto → recolección (picking name/origin) → contacto (ref/name) → tipo de operación (code/name)** con `action_id` para botón "Abrir"; **modos** Operaciones/Contar inventario (`/modes` → action-410/396); layout con tips y jerarquía tipo EE. Tests (7 ✓) con picking rename determinista.
- **Verificación**: 16/16 tests verdes en la tanda; browser: ALQ200 6 cards, SUBS200 MRR, BARRAS200 modos→acciones reales + scan `PRD-001` card, **consola 0 errores**; capturas `qa/shots/v2-{alq,subs,barras}.png`.
- Gotchas de la tanda: `Environment` sin `.sudo()` otra vez (v2 lo reintrodujo); type de acción real = `'ir.actions.act_window'` (usar ilike); dominios OR v20 = leaf tuple + `"|"` plano (el valor de `in` va DENTRO del leaf); compute sin `@api.depends` cachea stale → depends obligatorio; `controllers/__init__` con import erróneo = registry CRITICAL (todas las rutas 404).
- Risk: item 3 (modelos/menús/contratos propios) — verificado tests+browser; item 1 sin cambios (facturas siguen en borrador). F5 queda como siguiente paso global tras "todos los módulos terminados".

### L25 — F5 hito 1: smoke POS, e2e sin residuo, diagnóstico de consola (2026-10-28)

- **L25** (verbatim): "vamos con 1 y 2" (F5 + gaps de producto).
- Evidencia F5 (tabla en `ce-coverage-matrix.md` §Estado F5): POS+Restaurante smoke ✓ (0 consola, capturas f5-pos*); e2e **suscripción→cron→2 facturas draft→limpieza total** ✓; e2e **alquiler→factura AR draft $302,50→limpieza** ✓; **CAE:177 posted con CAE** ✓; compra CSV ya probado (L17); `hr` sin repro (transitorio L22); **`hr_recruitment` = bug CORE** (`SettingsPage.SidePanel` reading 'key', repro 100%, no nuestro) → matriz actualizada con leyenda B/C/P/CORE.
- Siguiente inmediato dentro de "2": specs Ventas/Manufactura + actividades en suscripciones (lote pequeño); luego gaps grandes (Taller/Declaración/OCR/IA-agentes) según tu prioridad.
- Risk: none (e2e con residuo cero y rollback; smoke y diagnósticos sólo lectura).

### L26 — F5 hito 1 cerrado + gaps lote 1 (2026-10-28)

- **F5 hito 1** (L25/commit168eb4c): POS+Restaurante smoke ✓, e2e sin residuo (suscripción cron y alquiler→factura) ✓, **CAE177** ✓, `hr` no-repro, **`hr_recruitment` = bug CORE web SettingsPage** (upstream), matriz con leyenda B/C/P/CORE.
- **Gaps lote 1** (commit siguiente): specs `ee-parity/{ventas,manufactura}.md` (CE alto: sólo KPI strip/estado-factura/onboarding faltan en Ventas; Manufactura atado a DOLAN_taller para "Siguiente actividad") + **actividades en DOLAN_suscripciones**: `_inherit mail.thread + mail.activity.mixin`, chatter en form, columna actividad (`activity_state` widget activity) — verificado por arquitectura (form chatter/followers/activities ✓, list actividad/vendedor/fase ✓) y tests 13/13 verdes (incluye message_post + activity_schedule con residuo nulo).
- Quedan (bloqueados por tu prioridad): **DOLAN_taller, Declaración fiscal AR, OCR de compras (F4), IA-agentes**, specs EE de Ayuda/Planificación/Aprobaciones si habilitás más módulos en la demo.
- Risk: none (chatter = mixins nativos propios; specs/docs; tests+arquitectura verificados).

### L27 — Decisiones para destrabar (2026-10-28)

Respuestas del dueño (batch de preguntas):
- **L27a**: construir los 4 gaps: DOLAN_taller, Declaración fiscal AR, OCR compras (F4), IA-agentes v1.
- **L27b**: OCR = motor **ChatGPT (cloud)** (token ya conectado).
- **L27c**: IA-agentes v1 = **con tool-loop** (permisos por herramienta, ítem 2).
- **L27d**: F5 hito 2 (matriz B→C) = **después de los gaps**.

Orden de construcción: OCR (usa infra existente) → Declaración fiscal → DOLAN_taller → IA-agentes. Feature doc nuevo: `odd/tasks/dolan-gaps.md` (Specs L27 verbatim).

### L28 — F5 hito 2: matriz B→C (2026-10-28)

- **Barrido dual** (oscuro como juan + claro como operador no-admin, navegación por rail con reintento): **36/38 apps C** en ambos perfiles con 0 errores de consola; explicaciones documentadas para el resto: 3 tableros DOLAN_* admin-only por diseño (403 correcto para operador), mail = client action (`.o_discuss`), website×3 = previews iframe/canvas, pos_restaurant = floor planner sin raíz propia, data_recycle flakiness del sweep (OK manual 10 filas).
- **Remedios**: grants al operador (account readonly/invoice, fleet user, sales_team salesman, hr_holidays user, crm, project, pos, mass_mailing, survey, lunch, etc.); tema por param oscuro→claro restaurado; `data_recycle` raíz sin grupos.
- **Matriz final** en `ce-coverage-matrix.md` §Estado F5 hito 2: sin filas NE ni P sin prueba; único pendiente no-propio = bug CORE hr_recruitment Ajustes (upstream).
- Evidencia: `qa/shots/f5h2/*.png` (dual por app), `rea/f5h2.json`, usuario `operador@dolan.com.ar` (id8) creado para verificación no-admin permanente.
- Risk: none (solo grants de lectura/uso al usuario de prueba propio + pruebas; cero cambios de código en este hito).

### L37a — Specs F1 restantes: no habilitables en la demo (2026-10-28)
- La demo EE (exalink) **no expone** Ayuda/Planificación/Aprobaciones/Calidad: no están en la grilla (26 tiles) ni en la búsqueda de Aplicaciones (no aparecen como instalables; el trial no los incluye). Intento de activación vía Playwright: `NO_CARD` para las 4.
- **Resolución**: quedan como pendientes documentados hasta que la cuenta EE tenga esos módulos habilitados (requiere suscripción/upgrade en odoo.com) — no se pueden spec-ear por observación.

### L38 — Opcionales v3 cerrados (2026-10-28)

- **Bancos v2**: segunda pasada sin filtro de partner + **sugerencias de conciliación manual** (candidatos listados por línea en el resultado del motor).
- **Barras v3**: soporte de **embalajes (packs)** condicionado a existencia de `product.packaging` (EE-only en esta build CE — hallazgo v20).
- **IA**: **Artículos de contexto** por agente (`dolan.ai.articulo`, activos se inyectan en el system prompt como contexto adicional).
- **Alquileres v3**: vista **calendario** de disponibilidad + tablero con **ingresos del mes / contratos / días alquilados**.
- **Suscripciones v3**: gráfico recurrente por plan/estado/fase.
- Fixes: graph sin dotted-measure (v20), `return` faltante en `_producto` tras refactor.
- **PR #4 mergeada** (`a0bbc87`), deploy verde: **89 tests** en el lote (55 ai + 7 barras + 9 alquileres + 5 bancos + 13 suscripciones), UI 200.
- Risk: none (mismas reglas de seguridad; vista/JS propios).

### L39 — Backups verificados de punta a punta (2026-10-28)

- **Backup completo ejecutado**: `backups/daily/dolan_20261028_171841.sql.gz` (7.2 MB, 544k líneas) + configs.
- **Prueba de fuego REAL**: restaurado en DB nueva `dolan_restaurada` → sanity completo (6 users, 512 moves, **189 con CAE**, 258 módulos instalados, 4 agentes IA, 5 prompts) → **Odoo arrancó con la DB restaurada y login OK (uid=7)** → cleanup de la DB de prueba.
- **Cron instalado**: diario 2AM (`0 2 * * *`) con retención 30 días + mensuales del día 1 (script ya los hacía); path del script actualizado a `/root/DOLAN_odoo20/odoo20-argentina`.
- Gotcha psql: `psql -U odoo` conecta a la DB "odoo" (que no existe) → comandos de mantenimiento requieren `-d postgres`.
- Risk: none (drop de una DB de prueba creada ad-hoc; producción intacta).
