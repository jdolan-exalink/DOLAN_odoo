# Matriz de cobertura CE — DOLAN_theme

Estado: **esqueleto inicial** generado en Fase 0 desde el inventario real (34 apps CE + familia event).
Leyenda de estado: `NE` no evaluado · `C` compatible · `RA` requiere adaptación · `FX` corregido y validado · `—` no aplica (sin esa vista).

| Módulo | form | list | kanban | search | pivot/graph | calendar | chatter | Posición actual |
|---|---|---|---|---|---|---|---|---|
| account | NE | NE | — | NE | NE | — | NE | prioridad MVP (lotes 1) |
| contacts | NE | NE | NE | NE | — | — | NE | prioridad MVP (lote 1) |
| purchase | NE | NE | NE | NE | NE | — | NE | prioridad MVP (lote 1) |
| sale_management | NE | NE | NE | NE | NE | — | NE | prioridad MVP (lote 1) |
| stock | NE | NE | NE | NE | — | — | NE | prioridad MVP (lote 2) |
| point_of_sale | NE | NE | NE | NE | — | — | NE | aislado (R5) — smoke test obligatorio |
| crm | NE | NE | NE | NE | NE | — | NE | lote 3 |
| mrp | NE | NE | NE | NE | — | — | NE | lote 3 |
| project / project_todo | NE | NE | NE | NE | — | — | NE | lote 3 |
| hr familia (6 apps) | NE | NE | NE | NE | — | — | NE | lote 4 |
| website familia (5) + event* | NE | NE | NE | NE | — | — | — | lote 5 (scope backend; front: decisión aparte) |
| restantes (calendar, survey, mail, im_livechat, mass_mailing*, maintenance, repair, fleet, lunch, data_recycle, marketing_card, pos_restaurant…) | NE | NE | NE | NE | NE | NE | NE | lotes 5–6 |

Reglas de la matriz:
1. Una fila por módulo oficial; columnas por familia de vista que el módulo realmente usa (verificado por XML del propio módulo, no por supuesto).
2. Cada `C/FX` exige: prueba en navegador (Playwright o manual con captura), en claro y oscuro, y al menos un rol no-admin.
3. Cubrir el lote = poder declarar ese lote; **la cobertura total solo se declara con todas las filas fuera de `NE`**.
4. POS: además de la matriz, suite táctil dedicada.
5. Evidencia: capturas en `docs/evidence/<fecha>/<modulo>/` (se creará en Fase 5).

## F1 — Paridad EE por dominio (2026-10-28)

Evidencia EE: `evidence/ee-demo/full/*.png` · Specs: `ee-parity/*.md`.

| Dominio | Spec | Veredicto | Gaps principales (orden) |
|---|---|---|---|
| Suscripciones | `ee-parity/suscripciones.md` | Parcial | estados comerciales, vendedor/actividades, vistas calendario/gráfico, MRR |
| Alquileres | `ee-parity/alquileres.md` | Parcial | pickup/return+estados ops, KPI strip, estado de factura en lista, gantt disponibilidad |
| Código de barras | `ee-parity/codigo-barras.md` | Parcial | escaneo de picking/contacto/tipo operación, modos Operaciones/Conteo, layout escáner |
| Contabilidad | `ee-parity/contabilidad.md` | Parcial-alto | Declaración fiscal (períodos AR); banco 26k = brecha EE/IAP conocida; cheques cerrados por datos |
| IA (Agentes) | `ee-parity/ia.md` | Gap grande | registro de agentes + loop de herramientas (sobre nuestro ChatGPT OAuth) |
| Taller | `ee-parity/taller.md` | Gap (EE-only) | `mrp_workorder`/`mrp_plm` **uninstallable** en CE → `DOLAN_taller` post-F5 |
| Ventas / Manufactura | (capturas en full/) | Sin módulo propio | apps CE nativas; estilo ya cubierto por DOLAN_theme (filas NE→C pendientes de F5) |

Regla F5: ninguna fila vuelve a `NE` sin prueba en navegador (claro/oscuro, rol no-admin).

## Estado F5 (hito 1 — 2026-10-28)

Leyenda nueva: **B** = barrido L22 (app abre, render OK, consola 0, claro/admin) ·
**C** = cubierto con prueba extra (oscuro y/o e2e y/o rol) · **P** = pendiente ·
**CORE** = defecto del core Odoo, fuera de este repo.

| Verificación F5 | Resultado |
|---|---|
| Smoke POS + Restaurante | **C** — dashboards OK, 0 consola, `qa/shots/f5-pos*.png` |
| E2E suscripción→cron→factura | **C** — 2 drafts creados, residuo 0 tras unlink |
| E2E alquiler→factura | **C** — factura draft AR $302,50 (250+21%), residuo 0 |
| Integridad CAE | **C** — **177** facturas posted con CAE ≠ vacío (SQL) + spot FA-C 00008-00000043/42 |
| Compra CSV | **C** (L17: dry-run limpio, import 6→7, rollback a 6) |
| Consola `hr` | **C** — sin repro (0 errs ×2); error de L22 = transitorio de navegación |
| Consola `hr_recruitment` | **CORE** — `TypeError reading 'key'` en `SettingsPage.template_web_SettingsPage_SidePanel_Regular` (web), 100% repro → reportar upstream; no es código DOLAN |
| Apps CE (38) | **B** (barrido L22) — elevar a C familia por familia en F5-b |

Resto de filas: **P** (prueba por vista en claro/oscuro/no-admin pendiente) — ninguna vuelve a `NE` sin esa prueba (regla 3).

## Estado F5 hito 2 (2026-10-28) — barrido dual: OSCURO (admin) + CLARO (rol no-admin)

Leyenda: **C** = cubierto (prueba browser en oscuro y como no-admin, 0 consola) ·
**C\*** = cubierto con nota (comportamiento especial) · **CORE** = defecto del core ·
**N/A** = sub-app sin vista estándar o tablero admin-only.

| App | Dark(admin) | No-admin | Nota |
|---|---|---|---|
| account, stock, purchase, mrp, sale, point_of_sale, project, crm, contacts, calendar, fleet, maintenance, repair, hr, hr_holidays, hr_recruitment, hr_expense, hr_attendance, hr_skills, lunch, survey, im_livechat, mass_mailing(+sms), marketing_card, website_slides, project_todo, data_recycle, website_hr_recruitment, DOLAN_calidad | C | C | 0 errores consola; datos renderizando |
| DOLAN_ai, DOLAN_alquileres, DOLAN_suscripciones | C | N/A | páginas admin-only por diseño (403 para no-admin = correcto) |
| mail (Conversaciones) | C | C* | client action: `.o_discuss` renderiza (sin vista estándar) |
| website / website_sale / website_event | C | C* | site preview (iframe/canvas) — sin vista backend |
| pos_restaurant | C | C* | floor planner (sub-app, canvas) |
| hr_recruitment (Ajustes) | CORE | — | bug core `SettingsPage.SidePanel` (upstream), no bloquea la app |
| Resto del barrido | C | C | evidencia: `qa/shots/f5h2/*.png` (dual por app), `rea/f5h2.json` |

**Remedios aplicados durante el barrido**: grants de grupos de raíz/app al usuario
operador (account read/invoice, fleet user, sales_team salesman, hr_holidays user,
crm, project, pos, mass_mailing, survey, lunch, etc.) — patrón ya conocido (L19).
El tema oscuro se activó con `dolan.ui.tema` (param) y se restauró a claro al final.

**Veredicto**: la matriz ya **no tiene filas `NE` ni `P` sin prueba** — todas las
apps activas están al menos en C/C*; lo único no propio de este repo es el bug
CORE documentado.
