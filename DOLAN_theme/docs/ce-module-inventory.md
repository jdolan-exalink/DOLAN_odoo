# Inventario de módulos oficiales CE — Odoo 20.0-20261015

Fuente: escaneo de `__manifest__.py` de los addons del core en la imagen oficial `odoo:20.0`
(693 manifests · **34 con `application: true`**, todos LGPL-3 = CE). Estado de la columna final:
`no evaluado` salvo indicación. Máquina de estados: no evaluado → compatible → requiere adaptación → corregido → validado.

## Aplicaciones CE (34) — base de cobertura

| App | Lic. | Estado | Notas |
|---|---|---|---|
| account (Facturación/Contabilidad) | LGPL-3 | no evaluado | presente además en DB productiva |
| calendar | LGPL-3 | no evaluado | |
| contacts | LGPL-3 | no evaluado | |
| crm | LGPL-3 | no evaluado | |
| data_recycle | LGPL-3 | no evaluado | herramienta, no vertical |
| fleet | LGPL-3 | no evaluado | |
| hr, hr_attendance, hr_expense, hr_holidays, hr_recruitment, hr_skills | LGPL-3 | no evaluado | familia RR.HH./Empleados/Ausencias/Gastos |
| im_livechat | LGPL-3 | no evaluado | |
| lunch | LGPL-3 | no evaluado | |
| mail (Mensajería/chatter) | LGPL-3 | no evaluado | crítico: chatter en todas las vistas |
| maintenance | LGPL-3 | no evaluado | Mantenimiento |
| marketing_card, mass_mailing, mass_mailing_sms | LGPL-3 | no evaluado | |
| mrp (Fabricación) | LGPL-3 | no evaluado | |
| point_of_sale, pos_restaurant | LGPL-3 | no evaluado | **riesgo táctil (R5)**; instalados en stack |
| project, project_todo | LGPL-3 | no evaluado | Proyectos |
| purchase (Compras) | LGPL-3 | no evaluado | instalado en stack |
| repair | LGPL-3 | no evaluado | Reparaciones |
| sale_management (Ventas) | LGPL-3 | no evaluado | instalado en stack |
| stock (Inventario) | LGPL-3 | no evaluado | instalado en stack |
| survey | LGPL-3 | no evaluado | Encuestas |
| website, website_event, website_hr_recruitment, website_sale, website_slides | LGPL-3 | no evaluado | **riesgo editor/visuales (R6)**; eCommerce=website_sale; Eventos: `event*` presentes como addons (no-flag application) |

## Familias del alcance — verificación de presencia

| Familia pedida | Presente en odoo:20.0 | Observación |
|---|---|---|
| Contactos / CRM / Ventas / Compras / Inventario / MRP / POS / Website / eCommerce / Proyectos / Empleados / Ausencias / Gastos / Mantenimiento / Reparaciones / Flota / Eventos / Encuestas / Calendario / Mensajería / Configuración | ✅ (tabla anterior o `base`) | Estado: no evaluado |
| Hojas de horas | ❓ `hr_timesheet` **no hallado** en addons del core de la imagen | verificar tras instalar bundle HR; posible ausencia/rename → documentar |
| Calidad | ❌ no está en core CE | existe como tile OEEL-1 `quality_control` (Enterprise) → **fuera de CE** |
| Ayuda/Helpdesk, Firma (sign), Studio, VoIP... | ❌ | tiles OEEL-1 (19 en la DB) — no CE; ya ocultos en stack productivo |

## Fuera del core (contexto del stack productivo, no parte de CE)

- Addons propios AR (`l10n_ar*` vía core + `l10n_ar_fiscal_ws` y ux/purchase de terceros AGPL) y módulos propios (`dolan_dash`, `dolan_ui`) — el tema debe verse bien con ellos instalados (matriz vertical).

## Siguiente paso

Detalle por módulo (menús, vistas, widgets, estados) en Fase 5 por lotes; la cobertura total **no** se decl hasta completar pruebas (política en `version-support-policy.md`).
