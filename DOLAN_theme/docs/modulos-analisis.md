# Análisis de módulos — activación total + REA (L22)

Fecha: 2026-10-28 · DB `dolan` (CE) y demo EE `exalink.odoo.com`.
Metodología: activación por lotes de TODAS las apps instalables (flag
`application`), barrido Playwright 38/38, y **MCP REA** vía CDP (Chromium
propio `:9222`): `inspect_web_page` (DOM/consola profunda) +
`observe_web_session` (ventana 40s con navegación de 10 apps).

## 1. Activación CE — 38/38 apps

- Lotes: A (hr_attendance, hr_holidays, hr_recruitment, lunch, repair, survey,
  data_recycle) → B (im_livechat, mass_mailing(+sms), marketing_card) →
  C (pos_restaurant) → D (website + website_sale/event/slides/hr_recruitment
  + 26 puentes `website_*`). UI200 tras cada lote; `application=true installed = 38`.

## 2. Barrido Playwright (38/38) — `rea/analysis_pw.json` + `qa/shots/analysis/*.png`

- **Status HTTP 200 en las 38 apps; 0 fallos de navegación; 0 errores de
  consola en 36**.
- **2 con error de consola**: `hr` y `hr_recruitment` →
  `TypeError: Cannot read properties of undefined (reading 'type')`
  (núcleo/localizado; queda como hallazgo a diagnosticar en F5).
- **Apps visibles (inicial)**: 20/32 apps con raíz propia visibles → tras **grants de
  grupos de raíz a juan** (patrón fleet/mrp/pos): +10 (crm, project,
  mass_mailing, hr_recruitment, marketing_card, website_slides, im_livechat,
  survey, hr_attendance, lunch) → **37/38** → `hr_holidays` exigió fix
  distinto: la raíz quedaba fuera del payload aunque el grupo ya estaba →
  **raíz sin acción derivable** (primer hijo `Mi tiempo` sin acción) → se le
  asignó la acción del primer hijo con acción (`hr.leave.report.calendar`) +
  ACL admin → **apps visibles (final 38/38)** (raíces propias32/32; las6 restantes son
  sub-apps sin raíz, p.ej. website_sale/pos_restaurant).
- Datos por app: título, registros listados, ruta aterrizada, errores.

## 3. REA (MCP) — evidencia

- **R1 `inspect_web_page`**: `ev_996edf38…` sobre la home (Operaciones KPI):
  HeadlessChrome/156, DOM 769 nodos (incl. `data-dolan-theme`), ventanas de
  consola/red, `policy_filtered` documentado (scripts/sin atributo → fuera de
  política) — limitaciones de REA registradas tal cual.
- **`observe_web_session`**: `ev_fd320cf5…` ventana 40s: **timeline 88 items**
  (lifecycle + `navigation_committed` por app: action-305 contabilidad → … →
  crm), `dropped_events.total = 0`, condición `attach_limited` (sólo
  metadata de navegación — por diseño la sesión NO retiene bodies/consola;
  la consola profunda la cubre `inspect_web_page`).
- Crónica: `/json/new` deshabilitado en Chrome156 → se condujo el target
  vía `connectOverCDP` (Playwright) durante la ventana REA.

## 4. Demo EE — grilla completa + apps clave (F1/R2)

Credenciales sólo por env (nunca en archivo). Grilla **26 tiles** en
`docs/evidence/ee-demo/full/00-grilla-apps.png`. Capturas clave (0 errores
consola): `suscripciones`, `alquiler` (Órdenes de alquiler), `ia`
(**Agentes**), `taller`, `código-de-barras`, `manufactura`, `ventas`,
`contabilidad` (Tablero).

Lectura de paridad:
- **Cobertura nuestra probada**: EE tiene Suscripciones/Alquiler/Código de
  barras → nuestros `DOLAN_suscripciones`, `DOLAN_alquileres`,
  `DOLAN_codigo_barras` (v1) enfrentan referencia directa (capturas para
  comparar campo a campo en F1).
- **EE "IA / Agentes"**: feature EE de agentes; nuestro `DOLAN_ai` =
  ChatGPT OAuth (decisión del usuario: sólo ChatGPT) → brecha acotada.
- **"Taller"** (workshop/servicios de campo): **sin equivalente nuestro** →
  nuevo gap candidato a F3.
- EE demo NO muestra Calidad en la grilla → `DOLAN_calidad` queda sin ref EE
  (diseño propio, aceptado).
- Grilla EE NO incluye Ayuda/Planificación/Aprobaciones en esta demo
  (módulos no habilitados) → documentar si habilitás más.

## 5. Artefactos

- CE: `rea/apps.json` (nav por app), `rea/analysis_pw.json` (38 filas),
  `qa/shots/analysis/*.png` (38), grants/fixes en Log L22.
- EE: `docs/evidence/ee-demo/full/*.png` (9).
- REA: evidence ids `ev_996edf…` (inspect) y `ev_fd320c…` (sesión).
