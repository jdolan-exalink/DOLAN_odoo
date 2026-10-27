# ROADMAP — Migración Dolibarr Argentina a Odoo 20 CE

Este roadmap convierte el PRD en un plan de desarrollo verificable para construir un stack Odoo 20 CE en Docker Compose, crear la base `dolan`, instalar los módulos requeridos, migrar las empresas y datos desde `/root/dolibarr`, y alcanzar paridad funcional con la operación Dolibarr actual.

## Decisión de arquitectura inicial

| Área | Decisión |
| --- | --- |
| Plataforma | Odoo 20 Community Edition sobre Docker Compose. |
| Base objetivo | PostgreSQL con base inicial `dolan`. |
| Fuente funcional | Dolibarr en `/root/dolibarr`, incluyendo documentación, módulos custom, datos y contratos operativos. |
| Estrategia | Reimplementar en addons Odoo usando ORM, reglas de acceso, vistas, QWeb/Owl, scheduled actions y colas. No copiar PHP como código productivo. |
| Localización | Crear una capa reutilizable de localización Argentina para multi-CUIT, ARCA, padrón, moneda, reportes e importación. |
| Migración | Migrar primero configuración y maestros; después saldos, stock y documentos históricos; validar con reportes de reconciliación. |
| Operación | Todo debe poder levantarse, inicializarse, respaldarse y restaurarse con Docker Compose y scripts versionados. |

## Objetivo operativo final

Al terminar el roadmap, un operador debe poder ejecutar un flujo equivalente a:

```bash
docker compose up -d
./scripts/init_odoo.sh --db dolan --install-all
./scripts/migrate_from_dolibarr.sh --source /root/dolibarr --db dolan
./scripts/healthcheck.sh
```

Resultado esperado:

- Odoo disponible en `http://localhost:<puerto>`.
- Base `dolan` creada y lista.
- Addons base, localización Argentina y módulos propios instalados.
- Empresas fiscales migradas desde Dolibarr.
- Clientes, proveedores, productos, bancos, cajas, depósitos, puntos de venta, certificados referenciados, saldos y stock importados según alcance aprobado.
- Validaciones de paridad funcional ejecutadas y documentadas.

## Fases del desarrollo

### Fase 0 — Discovery técnico y congelamiento de alcance

**Objetivo:** convertir el PRD y Dolibarr actual en una matriz de paridad implementable.

**Entradas principales:**

- `PRD-ERP-ARGENTINA.md`
- `/root/dolibarr/README.md`
- `/root/dolibarr/IMPLEMENTATION_STATUS.md`
- `/root/dolibarr/IMPLEMENTATION_PLAN.md`
- `/root/dolibarr/docs/ARCA.md`
- `/root/dolibarr/docs/MULTICOMPANY.md`
- `/root/dolibarr/docs/TAKEPOS.md`
- `/root/dolibarr/custom/arcaargentina/`
- `/root/dolibarr/custom/cloverbridge/`
- `/root/dolibarr/mercadopago/`
- `/root/dolibarr/import-templates/`

**Entregables:**

- Matriz Dolibarr → Odoo por módulo, flujo, modelo, dato, permiso y reporte.
- Inventario de datos migrables y datos excluidos por seguridad.
- Lista de módulos Odoo CE estándar a instalar.
- Lista de addons propios a desarrollar.
- Decisiones pendientes documentadas en `DECISIONS.md` o documento equivalente.

**Criterios de aceptación:**

- Cada funcionalidad Dolibarr actual tiene destino definido: Odoo estándar, addon propio, migración de datos, integración externa, o fuera de alcance.
- Las tres entidades fiscales actuales quedan identificadas con CUIT, condición fiscal, PV, certificados, cajas, bancos y depósitos.
- Los secretos fiscales quedan expresamente excluidos del repositorio y de los dumps versionados.

---

### Fase 1 — Stack Docker Compose de Odoo

**Objetivo:** crear el entorno reproducible para desarrollo y operación.

**Componentes mínimos:**

- `odoo`: Odoo 20 CE.
- `postgres`: PostgreSQL persistente.
- `worker` o cola equivalente si se adopta queue job.
- `cron`: ejecución programada de tareas Odoo o contenedor auxiliar si corresponde.
- `backup`: respaldo de PostgreSQL, filestore y configuración operativa.
- Volúmenes para `odoo_data`, `postgres_data`, `addons`, `backups` y `secrets`.

**Entregables:**

- `docker-compose.yml`
- `.env.example`
- `config/odoo.conf`
- `addons/` para módulos propios.
- `scripts/init_odoo.sh`
- `scripts/backup.sh`
- `scripts/restore.sh`
- `scripts/healthcheck.sh`

**Criterios de aceptación:**

- `docker compose up -d` levanta Odoo y PostgreSQL.
- La base `dolan` se crea de forma idempotente.
- El filestore y PostgreSQL sobreviven a reinicios.
- Los secretos no se montan desde rutas versionadas con contenido sensible.
- `healthcheck.sh` valida web, base, addons path, filestore y conectividad interna.

---

### Fase 2 — Bootstrap Odoo y módulos base

**Objetivo:** inicializar `dolan` con configuración regional Argentina y módulos base.

**Módulos Odoo CE esperados:**

- `base`
- `web`
- `mail`
- `contacts`
- `account`
- `sale_management`
- `purchase`
- `stock`
- `point_of_sale`
- `crm`
- `project` si aplica por paridad.
- `mrp` si la matriz confirma uso productivo.
- `l10n_ar` y `l10n_latam_invoice_document` si están disponibles y compatibles con Odoo 20 CE.
- Addons propios de localización y migración.

**Entregables:**

- Script idempotente de instalación de módulos.
- Configuración de idioma, zona horaria, moneda ARS, compañías y plan contable inicial.
- Addon base `l10n_ar_dolan_base` para convenciones compartidas.

**Criterios de aceptación:**

- `./scripts/init_odoo.sh --db dolan --install-all` puede ejecutarse más de una vez sin duplicar configuración crítica.
- Odoo muestra ARS, Argentina y zona horaria correcta.
- Los módulos base quedan instalados y actualizables desde CLI.

---

### Fase 3 — Fundación multiempresa / multi-CUIT

**Objetivo:** modelar tres o más entidades fiscales con aislamiento operativo.

**Alcance:**

- Compañías Odoo por entidad fiscal.
- Perfiles fiscales por CUIT.
- Puntos de venta por compañía.
- Certificados ARCA referenciados por compañía, nunca versionados.
- Cajas, bancos, diarios contables y depósitos separados.
- Reglas de acceso por compañía y rol.

**Addons sugeridos:**

- `l10n_ar_dolan_base`
- `l10n_ar_dolan_multicuit`
- `dolan_security_audit`

**Criterios de aceptación:**

- Un usuario de una empresa no puede facturar ni operar caja con certificados, PV, bancos o depósitos de otra empresa.
- Los reportes consolidados requieren permiso explícito.
- POS y documentos muestran empresa, CUIT y PV activo.

---

### Fase 4 — Facturación electrónica ARCA / WSAA / WSFEv1

**Objetivo:** emitir comprobantes fiscales con CAE desde `account.move`.

**Alcance funcional:**

- WSAA: autenticación por certificado.
- WSFEv1: autorización de Facturas A/B/C y NC/ND.
- Persistencia de CAE, vencimiento, QR fiscal y respuesta completa sanitizada.
- Idempotencia por factura y punto de venta.
- Cola o tarea programada para comprobantes pendientes.
- Homologación antes de producción.

**Addons sugeridos:**

- `l10n_ar_dolan_arca`
- `l10n_ar_dolan_fiscal_document`
- `dolan_integration_job`

**Criterios de aceptación:**

- Una factura válida obtiene CAE y no duplica autorización al reintentar.
- Una factura rechazada conserva diagnóstico accionable sin corromper saldo ni stock.
- Logs no exponen claves privadas, certificados completos ni tokens sensibles.
- QR fiscal aparece en PDF/ticket según normativa vigente.

---

### Fase 5 — Padrón ARCA y perfiles fiscales de terceros

**Objetivo:** consultar CUIT y autocompletar datos fiscales de clientes/proveedores.

**Alcance:**

- Consulta por CUIT.
- Cache con fecha, usuario, fuente y expiración.
- Autocompletado de razón social, domicilio y condición fiscal cuando esté disponible.
- Manejo de servicio caído, CUIT inválido, límites y respuestas parciales.

**Addon sugerido:**

- `l10n_ar_dolan_padron`

**Criterios de aceptación:**

- Una consulta exitosa actualiza el tercero y registra auditoría.
- Una consulta fallida no bloquea la operación manual si el rol lo permite.
- La política de cache evita consultas repetitivas innecesarias.

---

### Fase 6 — Monedas y cotización del dólar

**Objetivo:** mantener cotizaciones históricas auditadas y aplicables a documentos.

**Alcance:**

- Fuente configurable de cotización.
- Registro de compra, venta, fecha, hora, fuente y vigencia.
- Sincronización programada.
- Corrección manual con permiso y auditoría.
- Uso en cotizaciones, facturas, pagos y reportes.

**Addon sugerido:**

- `l10n_ar_dolan_currency`

**Criterios de aceptación:**

- La sincronización crea cotizaciones sin duplicados para la misma fuente/fecha.
- La corrección manual queda auditada.
- Los documentos muestran el tipo de cambio aplicado.

---

### Fase 7 — POS, cajas, medios de pago y Mercado Pago

**Objetivo:** llevar el circuito de mostrador Dolibarr/TakePOS a Odoo POS.

**Alcance:**

- POS con empresa, CUIT, PV, caja y usuario visibles.
- Efectivo, bancos, tarjetas, transferencias, Mercado Pago, cheques y cuenta corriente según matriz.
- Apertura, arqueo, cierre y reporte Z.
- Webhook/IPN idempotente para Mercado Pago.
- Conciliación con banco/caja por compañía.

**Addons sugeridos:**

- `dolan_pos_fiscal_context`
- `dolan_payment_instruments`
- `dolan_mercadopago`

**Criterios de aceptación:**

- No se puede cambiar de empresa durante una venta abierta.
- Una venta POS emite comprobante fiscal con CAE cuando corresponde.
- Un webhook repetido de Mercado Pago no duplica cobros.
- El cierre de caja concilia medios de pago por compañía.

---

### Fase 8 — Ventas, compras, stock, remitos y PDFs localizados

**Objetivo:** cubrir el circuito comercial completo con trazabilidad y documentos argentinos.

**Alcance:**

- Presupuesto → pedido → entrega/remito → factura → cobro.
- Solicitud/orden de compra → recepción → factura proveedor → pago.
- Egreso de stock solo con entrega/remito autorizado.
- Depósitos, movimientos, costos, inventario y trazabilidad.
- PDFs localizados: presupuesto, remito, recibo, factura/ticket.

**Addons sugeridos:**

- `dolan_stock_dispatch_policy`
- `dolan_report_templates_ar`

**Criterios de aceptación:**

- El stock no egresa por factura si la política requiere remito.
- Remitos y facturas quedan vinculados.
- Los PDFs contienen datos fiscales, empresa, CUIT, PV y numeración correcta.

---

### Fase 9 — Reportes fiscales, importaciones y migración de datos

**Objetivo:** migrar desde Dolibarr y producir reportes reconciliables.

**Orden recomendado de migración:**

1. Configuración base y compañías.
2. Usuarios, roles y permisos.
3. Clientes y proveedores.
4. Productos, UoM, precios e impuestos.
5. Bancos, cajas, diarios y depósitos.
6. Stock inicial y saldos.
7. Documentos abiertos.
8. Documentos históricos definidos como legalmente necesarios.
9. Adjuntos/PDFs, solo si el alcance legal/operativo lo requiere.

**Entregables:**

- `scripts/export_dolibarr_*` o adaptadores de lectura documentados.
- `scripts/migrate_from_dolibarr.sh`
- Addon `dolan_migration`
- Reporte de validación por lote.
- Rollback por lote o restauración documentada.

**Criterios de aceptación:**

- Cada lote de migración informa creados, actualizados, rechazados y errores por fila.
- Clientes/proveedores/productos migrados tienen claves externas para reintentos idempotentes.
- Saldos, stock y comprobantes migrados tienen reporte de diferencias.
- La migración nunca importa secretos fiscales desde Dolibarr.

---

### Fase 10 — Hardening, observabilidad y producción

**Objetivo:** dejar el sistema operable con seguridad, backup, restore y trazabilidad.

**Alcance:**

- Backups diarios con retención configurable.
- Restore ensayado en entorno limpio.
- Healthchecks para web, DB, filestore, cron, colas e integraciones externas.
- Sanitización de logs.
- Rotación de credenciales y certificados documentada.
- Runbooks de actualización y rollback.

**Criterios de aceptación:**

- Un backup puede restaurar `dolan` en un entorno limpio.
- El healthcheck distingue fallos de Odoo, DB, ARCA, moneda, cron y filestore.
- Hay guía operativa para homologación y producción.

---

## Épicas de implementación sugeridas

| Épica | Resultado | Dependencias |
| --- | --- | --- |
| Infra Docker | Stack Odoo reproducible con DB `dolan`. | Ninguna. |
| Bootstrap Odoo | Módulos base instalados y configuración Argentina inicial. | Infra Docker. |
| Multi-CUIT | Compañías, fiscal profiles, PV, bancos, cajas y depósitos aislados. | Bootstrap Odoo. |
| ARCA | Facturación electrónica con CAE, QR e idempotencia. | Multi-CUIT. |
| Padrón | Consulta CUIT y autocompletado fiscal. | Multi-CUIT. |
| Currency | Cotización dólar sincronizada y auditada. | Bootstrap Odoo. |
| POS/Pagos | POS fiscalizado, cajas, Mercado Pago y conciliación. | Multi-CUIT, ARCA, Currency. |
| Comercial/Stock | Circuitos venta/compra/remito/stock/PDFs. | Bootstrap Odoo, Multi-CUIT. |
| Migración | Datos Dolibarr importados y reconciliados. | Modelos destino estables. |
| Producción | Backup/restore, healthchecks, runbooks y seguridad. | Todas las anteriores. |

## Primer corte recomendado

Para arrancar sin abrir demasiados frentes, el primer hito debe ser:

**Hito 1 — Odoo levanta con `dolan` y módulos base instalados**

Incluye solamente:

- Docker Compose.
- `.env.example`.
- `config/odoo.conf`.
- `scripts/init_odoo.sh`.
- `scripts/healthcheck.sh`.
- Estructura `addons/`.
- Base `dolan` creada.
- Instalación automática de módulos Odoo CE mínimos.

No incluye todavía ARCA, migración ni POS custom. Eso evita mezclar infraestructura con reglas fiscales y reduce el riesgo de debugging cruzado.

## Riesgos principales

| Riesgo | Mitigación |
| --- | --- |
| Odoo 20 CE no está disponible actualmente como `odoo:20.0` en Docker Hub; el smoke test del Hito 1 usó `odoo:19.0`. | Definir imagen exacta o build propio de Odoo 20 antes de desarrollar módulos productivos. |
| La documentación Dolibarr no es totalmente consistente: README menciona v20 LTS, pero el Compose/estado observado usa `dolibarr/dolibarr:23.0.3`. | Tratar `/root/dolibarr/docker-compose.yml` e `IMPLEMENTATION_STATUS.md` como evidencia operacional actual hasta reconciliar la documentación. |
| Paridad Dolibarr incluye módulos custom y overrides no triviales. | Matriz de paridad obligatoria antes de prometer equivalencia completa. |
| Secretos ARCA existentes no deben migrarse ni versionarse. | Migrar referencias/configuración; cargar secretos manualmente o por volumen seguro. |
| Multiempresa mal configurada puede filtrar certificados, bancos o documentos. | Reglas de acceso, pruebas por rol y validaciones de compañía desde el inicio. |
| CloverBridge/MP Point depende de rutas Apache y un boundary HTTPS externo; Compose solo no alcanza para producción. | Separarlo como integración de fase posterior con prueba de punta a punta. |
| Facturación electrónica requiere homologación externa. | Separar modo homologación/producción y diseñar reintentos idempotentes. |
| Migración histórica puede ser legalmente sensible. | Definir qué documentos deben ser reproducibles y qué queda como archivo consultivo. |

## Checklist de inicio del desarrollo

- [ ] Confirmar imagen/base de Odoo 20 CE a usar.
- [ ] Crear stack Docker Compose mínimo.
- [ ] Crear base `dolan` de forma idempotente.
- [ ] Instalar módulos Odoo CE mínimos.
- [ ] Documentar addons propios necesarios.
- [ ] Construir matriz de paridad Dolibarr → Odoo.
- [ ] Definir política de secretos y certificados.
- [ ] Definir estrategia de migración por lote.
- [ ] Definir pruebas de reconciliación.

## Próximo paso

Implementar el **Hito 1 — Odoo levanta con `dolan` y módulos base instalados**. Ese hito debe producir el primer stack ejecutable y comprobar que la plataforma base está sana antes de desarrollar localización, ARCA o migración.
