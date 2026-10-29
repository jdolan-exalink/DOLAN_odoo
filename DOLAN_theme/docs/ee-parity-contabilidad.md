# Paridad CE ↔ EE — App "Contabilidad"

**Fecha**: 2026-10-29 · **Origen**: S8 (ver abajo en `odd/tasks/dolan-theme.md`)
**Pedido del usuario (verbatim)**: "contabilidad no esta y creeria que lo que paso es que renombraste para ponerle facturacion, quiero que via MCP REA trabajemos para que Contabilidad quede igual con las mismas funciones que el de la demo"

## 1. Evidencia

| Fuente | Cómo | Artefacto |
|---|---|---|
| Demo EE `exalink.odoo.com` | MCP REA `capture_browser_scenario` (login + `goto` a `/web/webclient/load_menus`, `capture.at_end=["dom"]`) | Evidence `ev_78bfb489fc80eb3ecb67747af1fa8388196d6779acb65059cc6a296979b26920`; árboles §2 y §3 |
| Nuestra BD `dolan` | `GET /web/webclient/load_menus` como `juan@dolan.com.ar` | árbol §4 |
| Captura visual previa | REA/Playwright L42 | `docs/evidence/ee-theme-v2/03-contabilidad.png` |
| Sustitutos CE disponibles | `ls odoo20-argentina/addons` + `ir_module_module` | §5 |

**Hallazgo sobre el "renombrado"**: no hubo renombre nuestro. En la demo la app es
`accountant.menu_accounting` (módulo **Enterprise `account_accountant`**, ruta `/odoo/accounting`,
acción 308). En CE ese módulo no existe; nuestra app contable es `account.menu_finance`
(nombre i18n "Facturación") con **42 nodos** visibles vs **97** de la demo.

**Segundo hallazgo**: en nuestra BD las secciones **Contabilidad** (151) y **Revisión** (156)
existen pero el menú está tras el grupo *"Show Accounting Features - Readonly"*, que
`juan@dolan.com.ar` **no** tiene → por eso "Contabilidad no está".

## 2. Demo EE — `accountant.menu_accounting` (97 nodos)

```
Contabilidad [action=308, ROOT]
  Tablero [action=308]
  Clientes: Facturas 267 · Notas de crédito 268 · Pagos 240 · Cheques de Terceros 451 · Productos 295 · Clientes 306
  Proveedores: Facturas 270 · Reembolsos 271 · Pagos 241 · Cheques Propios 450 · Productos 296 · Proveedores 307
  Contabilidad
    Transacciones: Asientos contables 264
    Activos y pasivos: Activos 464 · Préstamos 480 · Flotilla 1102
    Bloqueando: Conciliar 328 · Declaración fiscal 382 · Fechas de bloqueo… 337
    Consultar factura en ARCA 458
  Revisión
    Control: Apuntes contables 263 · Pista de auditoría 315 · Auditoría de diario 359
    Auditoría: Archivos de trabajo 389 · Reporte anual 968
    Inventario: Valuación de inventario 313
    Asientos de regularización: Ingresos diferidos 371 · Gastos diferidos 370
    Compras: Facturas por cobrar 689 · Facturado pero no recibido 690
    Ventas: Facturas por emitir 528 · Facturado y no entregado 529
  Reportes
    Reportes de estados de cuenta: Balance general 354 · Estado de resultados 356 · Flujo de efectivo 353 · Depreciación 470
    Libros contables: Balance de comprobación 364 · Libro mayor 360
    Reportes del contacto: Libro mayor empresa 365 · Estado de cuenta cliente 366 · Cobrar vencida 362 · Pagar vencida 363
    Impuestos y finanzas: Declaración fiscal 358 · Reporte fiscal 395
    Gestión: Análisis de facturas 299 · Flujo de efectivo 287 · Analítico 297 · Resumen ejecutivo 355 · Préstamos 481
    Informes Argentinos: Resumen IVA 462 · IIBB ventas 456 · IIBB compras 457
  Configuración
    Ajustes 303 · Pagos en línea 226
    Contabilidad: Plan de cuentas 280 · Impuestos 290 · Diarios 282 · Monedas 63 · Posiciones fiscales 305 ·
                   Varios libros mayores 283 · Revisiones 387 · Modelos de depreciación 468 · Tipos de devolución 381 ·
                   Recordatorios de facturas 399 · Tipos de Documentos 452
    Facturación: Términos de pago 292 · Categorías de productos 189
    ARCA: Tipos de documentos 455 · Responsabilidad 453 · Actividades 454 · Escala de ganancias 461
```

## 3. Nuestra app — `account.menu_finance` (42 nodos visibles para juan)

```
Facturación [action=264, ROOT]
  Clientes: Facturas 264 · Notas de crédito 265 · Pagos 237 · Productos 292 · Clientes 303
  Proveedores: Facturas 267 · Reembolsos 268 · Pagos 238 · Productos 293 · Proveedores 304
  Tablero DOLAN 859 · Escanear compra (IA) 1206 · Conciliación de bancos (IA) 1207
  Reportes > Gestión: Análisis de facturas 296 · Análisis de flujo de efectivo 284
  Configuración
    Ajustes 300 · Pagos en línea 223
    Contabilidad: Impuestos 287 · Diarios 279 · Monedas 63 · Posiciones fiscales 302 · Tipos de Documentos 345
    Facturación: Términos de pago 289 · Categorías de productos 189
    ARCA: Tipos de documentos 348 · Responsabilidad 346 · Actividades 347 · Web services (Servicios/Certificados/Tickets) · Conceptos 359 · Impuestos 360

Ocultos para juan (grupo "Show Accounting Features - Readonly"):
  Contabilidad 151 > Transacciones > Asientos contables 153 · Bloqueando > Proteger asientos 187
  Revisión 156 · Banco y Caja 197
```

## 4. Clasificación (demo → CE)

| # | Demo (EE) | Estado en CE | Vía |
|---|---|---|---|
| C1 | App "Contabilidad" | ❌ se llama "Facturación" | renombre propio LGPL del nombre de `account.menu_finance` |
| C2 | Secciones Contabilidad / Revisión | ✅ existen, ocultas por grupo | otorgar `Show Accounting Features - Readonly` al rol o bajar el grupo del menú |
| C3 | Asientos contables, Proteger/Fechas de bloqueo, Conciliar | ✅ en `account` CE (parcial: Conciliar y fechas están en Core/Banco) | exponer menús equivalentes |
| C4 | Clientes/Proveedores completos + Productos | ✅ | ya está |
| C5 | Cheques de Terceros / Cheques Propios | 🟡 `l10n_latam_check`, `l10n_latam_check_ux`, `account_cashbox_l10n_latam_check` (disponibles, sin instalar) | instalar + menús |
| C6 | Estados de cuenta (cliente vencido, por cobrar/pagar vencido) | 🟡 `account_debt_report` (disponible, sin instalar) | instalar + menús |
| C7 | Resumen IVA / IIBB por jurisdicción | 🟡 `l10n_ar_fiscal_ws_reports`, `l10n_ar_tax*` (disponibles) | instalar + verificar salida |
| C8 | Plan de cuentas, Revisiones, Recordatorios, Depreciación, Tipos de devolución (Config. Contabilidad) | 🟡 `account` CE los trae en otros menús; 2-3 son EE (`account_reports`/`account_accountant`) | reordenar menús propios |
| C9 | Tablero EE (onboarding, escaneo IA, banco, cheques) | 🟡 parcial: ya tenemos Tablero DOLAN + escaneo IA + conciliación bancos | ampliar tarjetas |
| C10 | Balance general, Estado de resultados, Flujo de efectivo, Balance de comprobación, Libro mayor, Resumen ejecutivo | 🔴 EE `account_reports` (licencia OPL-1, no copiable) | OCA `account_financial_report` (no está en el repo → requiere clonar) o implementación propia |
| C11 | Archivos de trabajo, Reporte anual, Pista de auditoría, Auditoría de diario | 🔴 EE | OCA `auditlog` / propio, o quedar fuera |
| C12 | Activos, Préstamos, Valuación de inventario, Ingresos/Gastos diferidos, Facturado no recibido/entregado | 🔴 EE `account_accountant` | parcial vía OCA, o fuera de alcance |
| C13 | "Consultar factura en ARCA" | 🟡 ya tenemos WSARCA en `l10n_ar_fiscal_ws` | exponer acción propia (query CAE) |

## 5. Plan propuesto

- **P1 (visible, bajo riesgo)**: app renombrada a **Contabilidad** + permisos para que se vean
  *Contabilidad* y *Revisión* + menús equivalentes de C3 → la app "se ve" como la demo.
- **P2 (funciones)**: cheques (C5), estados de cuenta (C6), informes argentinos (C7),
  consulta ARCA (C3/C13), tablero con las tarjetas que replicamos (C9).
- **P3 (decisión de alcance)**: reportes financieros y auditoría (C10-C12) → requieren clonar
  OCA (`account_financial_report`, `auditlog`) o implementación propia LGPL; **nada de código EE**.

## 6. Riesgos

- Risk: item 3 (menús/permisos compartidos del módulo `account`) → verificar por rol admin y no-admin.
- Instalar módulos nuevos = item 5 (dependencias/entorno) si se suma OCA.

## 7. Estado de implementación (2026-10-29)

| Ítem | Estado | Evidencia |
|---|---|---|
| C1 app "Contabilidad" | ✅ hecho | `account.menu_finance` = Contabilidad (en_US+es_AR), `/odoo/accounting`; commit `8ca82e1` |
| C2 secciones Contabilidad/Revisión/Reportes/Banco y Caja | ✅ hecho | implicación `group_account_manager → group_account_user`; QA 19/19 |
| C3 Asientos/Apuntes/Pista de auditoría | ✅ hecho | visibles para el admin tras C2 |
| C5 Cheques de Terceros / Propios | ✅ hecho | `l10n_latam_check` (core) instalado: menús en Clientes y Proveedores, igual que la demo |
| C6 Estados de cuenta | ✅ hecho | OCA `partner_statement` (19.0, portado) + 3 menús en Reportes > Reportes del contacto |
| C7 IIBB por jurisdicción | ✅ ya existía | `l10n_ar` (Reportes > Informes Argentinos) |
| C7 Resumen IVA | 🔴 bloqueado | `l10n_ar_fiscal_ws_reports` necesita port **fiscal**: la vista SQL y `_get_partner_document_code_and_number()` usan `res.partner.l10n_latam_identification_type_id`, eliminado en Odoo 20 → decisión sobre cómo derivar el código de documento en los TXT ARCA |
| C13 Consultar factura en ARCA | ✅ hecho | menú propio sobre `l10n_ar_fiscal_ws.action_fiscal_ws_recover` |
| C9 tablero con tarjetas | 🟡 pendiente | ampliar `dolan_dash` (fuera de este corte) |
| C10 estados financieros (Balance/ER/Flujo/Libro mayor) | 🔴 bloqueado | OCA `account_financial_report` 19.0 requiere port real: Odoo 20 **eliminó el modelo `account.group`** que usa para agrupar el balance |
| C11 auditoría | 🔴 bloqueado | OCA `auditlog` 19.0: Odoo 20 exige tabla para todo modelo no abstracto (`auditlog.log.line.view` es una vista SQL) |
| C12 Activos/Préstamos/Valuación/regularizaciones | 🔴 EE-only | fuera de alcance (licencia) |

### Ports Odoo 19.0 → 20.0 aplicados (reproducibles en el deploy)
1. `security/ir.model.access.csv` → `security/ir.access.csv` y columnas `perm_read/write/create/unlink` → una sola columna `operation` (letras `c`,`r`,`u`,`d`).
2. Reglas `model="ir.rule"` → `model="ir.access"` + `domain_force` → `domain` + `<field name="operation">crud</field>` (y quitar `global`).
3. Imports: `odoo.http.content_disposition` → `odoo.http.stream.content_disposition`; `odoo.http.serialize_exception` → `odoo.http.dispatcher.serialize_exception`.
4. `ir.actions.report.report_file` eliminado → quitar el campo del XML.
5. Manifests `version` 19.0.x → 20.0.x + `installable: True`.

### Sin portar (bloqueados, ver §7)
- `account_financial_report` (modelo `account.group` eliminado en Odoo 20).
- `auditlog` (modelo SQL-view sin tabla).
- `l10n_ar_fiscal_ws_reports` (identificación del partner eliminada → decisión fiscal).
