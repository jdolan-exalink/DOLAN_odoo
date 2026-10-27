# PRD — Odoo 20 CE con paridad funcional y localización Argentina

**Estado:** Borrador base para discovery técnico
**Fuente funcional:** `/root/dolibarr`
**Producto destino:** `/root/odoo20`
**Plataforma destino:** Odoo 20 Community Edition
**Idioma:** Español

## 1. Visión
Construir sobre Odoo 20 CE un ERP/CRM multiempresa para Argentina que conserve la cobertura funcional de Odoo Community y agregue las capacidades desarrolladas en Dolibarr: facturación electrónica ARCA, consulta de padrón, cotización del dólar, multi-CUIT, POS, logística, cobranzas, reportes fiscales y operación segura.

## 2. Objetivos
- Alcanzar paridad funcional con los módulos estándar instalados de Odoo 20 CE.
- Soportar múltiples entidades fiscales con aislamiento de datos, numeración, certificados y puntos de venta.
- Emitir comprobantes electrónicos mediante ARCA/WSFEv1 y obtener CAE.
- Automatizar consulta de contribuyentes en el padrón ARCA.
- Mantener cotizaciones históricas de monedas, incluyendo dólar.
- Proveer trazabilidad, auditoría, backups y operación preparada para producción.

## 3. No objetivos iniciales
- Reemplazar servicios oficiales de ARCA.
- Guardar claves privadas en el repositorio.
- Migrar datos productivos sin un plan de mapeo, validación y rollback.
- Copiar código PHP de Dolibarr sin adaptar contratos, seguridad, permisos y modelo de datos de Odoo.

## 4. Alcance funcional

### 4.1 Odoo 20 CE base — paridad
Inventariar y especificar equivalencia para: usuarios y permisos; compañías; clientes y proveedores; productos, variantes, unidades y listas de precios; cotizaciones; pedidos; entregas; facturas y notas de crédito/débito; compras y recepción; almacenes y stock; manufactura; proyectos; activos; contabilidad, impuestos, cuentas por cobrar/pagar; bancos y conciliación; pagos; POS; CRM; soporte/helpdesk disponible en CE o addon propio; reportes; workflows/acciones automatizadas; importación/exportación; auditoría y notificaciones.

Cada módulo debe tener: flujo actual de Odoo 20 CE, comportamiento requerido, grupos de seguridad, estados, modelos/vistas afectados, reportes, API, migración, pruebas y criterios de aceptación.

### 4.2 Localización argentina reutilizable

#### Facturación electrónica ARCA
- Integración WSAA para autenticación y WSFEv1 para autorización.
- Certificado X.509, clave privada y credenciales por entidad fiscal.
- Puntos de venta independientes.
- Tipos A, B, C, notas de crédito y débito, según condición fiscal.
- Solicitud y persistencia de CAE, fecha de vencimiento y respuesta completa.
- QR fiscal conforme a normativa vigente.
- Reintentos idempotentes, correlación, logs sanitizados y modo homologación/producción.
- Validación de CUIT, condición frente a IVA, moneda, impuestos y numeración.
- Cola para comprobantes pendientes y tarea programada equivalente a `request_pending_cae.php`.

**Código fuente de referencia:** `custom/arcaargentina/class/`, `core/modules/facture/`, `core/triggers/`, `ajax/arca_cae.php`, `wsdl/`.

#### Consulta de padrón ARCA
- Consulta por CUIT.
- Autocompletado de razón social, domicilio, condición fiscal y datos disponibles.
- Cache con fecha de consulta y política de expiración.
- Manejo de CUIT inexistente, servicio caído, límites y respuestas parciales.
- Permisos y auditoría de consultas.

**Referencia:** `ajax/check_padron.php`, `js/padron_autofill.js`, `test_padron.php`, `wsdl/personaServiceA13.wsdl`.

#### Cotización del dólar y monedas
- Cotizaciones oficiales configurables por fuente.
- Registro de compra/venta, fecha, hora, fuente y vigencia.
- Conversión en cotizaciones, facturas, pagos y reportes.
- Corrección manual con autorización y auditoría.
- Sincronización programada y tolerancia a fallos.

**Referencia:** `ajax/sync_dolar.php`, `cron/sync_currency.php`, `lib/currency.lib.php`, `js/currency_helper.js`, `admin/currencies.php`.

#### Multiempresa / multi-CUIT
- Tres o más entidades fiscales configurables.
- Aislamiento de certificados, numeradores, cuentas, cajas, bancos, depósitos y puntos de venta.
- Contexto de empresa visible en POS y documentos.
- Restricción por rol y empresa.
- Reportes consolidados únicamente para usuarios autorizados.

**Referencia:** `multicompany/`, `set_empresa.php`, `docs/MULTICOMPANY.md`.

#### POS y medios de pago
- POS táctil con empresa, CUIT y PV activo visibles.
- Efectivo, bancos, tarjetas, Mercado Pago y cheques.
- Cierre de caja, arqueo, liquidación y conciliación.
- Integración Mercado Pago mediante webhook/IPN idempotente.

**Referencia:** `docs/TAKEPOS.md`, `mercadopago/`, `cloverbridge/`, `arcaargentina/cheques.php`, `lib/payment_instruments.lib.php`.

#### Ventas, compras, stock y logística
- Circuito presupuesto → pedido → entrega/remito → factura → cobro.
- Circuito solicitud/orden de compra → recepción → factura → pago.
- Egresos de stock únicamente con entrega/remito autorizado.
- Depósitos, movimientos, trazabilidad, costos e inventarios.
- PDFs localizados de remito, recibo, presupuesto y comprobante.

**Referencia:** `core/modules/expedition/`, `core/modules/propale/`, `core/modules/paiement/`, `docs/TAKEPOS.md`.

#### Reportes e importaciones
- IVA, ventas, compras, impuestos, retenciones/percepciones y consolidado multiempresa.
- Importación de contactos, proveedores, productos, precios, stock, bancos y comprobantes.
- Historial, validación previa, errores por fila, reanudación y rollback.

**Referencia:** `reports/`, `retenciones.php`, `import_*.php`, `import-templates/`.

## 5. Requisitos no funcionales
- Seguridad: secretos fuera del repositorio, cifrado en reposo, mínimo privilegio, rotación y sanitización de logs.
- Disponibilidad: reintentos, colas, health checks y recuperación ante fallos externos.
- Integridad: idempotencia para autorización ARCA, pagos y webhooks.
- Auditoría: usuario, empresa, timestamp, payload resumido, resultado y correlación.
- Rendimiento: búsquedas de padrón y POS con respuesta interactiva; sincronizaciones fuera del request.
- Backup: rutina diaria, retención configurable, restauración ensayada y rollback de actualizaciones.
- Compatibilidad: zona horaria Argentina, ARS, IVA 21%/10,5% y formatos locales.

## 6. Modelo de datos mínimo
Entidades: CompanyFiscal, TaxIdentity, FiscalCertificate, PointOfSale, FiscalDocument, FiscalAuthorization, CustomerTaxProfile, PadronQuery, ExchangeRate, WarehousePolicy, CashRegister, PaymentInstrument, ImportBatch, AuditEvent y IntegrationJob. Todas las entidades fiscales deben incluir `company`, estado, auditoría y claves de idempotencia donde corresponda.

## 7. Roles
Administrador global; administrador fiscal; facturación; ventas; compras; depósito; cajero POS; tesorería; contador/auditor; consulta. Los permisos deben limitar empresa, operación, aprobación y acceso a secretos.

## 8. Migración desde Dolibarr
1. Inventariar módulos y dependencias.
2. Mapear entidades Dolibarr a modelos Odoo.
3. Extraer datos sin secretos.
4. Validar CUIT, numeración, saldos, stock y documentos.
5. Migrar primero catálogo y maestros; luego saldos y documentos históricos.
6. Ejecutar pruebas de reconciliación y generar informe de diferencias.
7. Migración productiva con backup, ventana y rollback.

**Regla:** reutilizar algoritmos, contratos funcionales, WSDL, fixtures y documentación; reimplementar la integración en Python sobre addons Odoo, usando el ORM, reglas de acceso, colas/tareas programadas, vistas XML/QWeb/Owl cuando corresponda, y respetando licencias y convenciones de Odoo.

## 9. Criterios de aceptación principales
- Una factura válida obtiene CAE y queda vinculada a la factura Odoo (`account.move`) sin duplicación al reintentar.
- Una factura rechazada conserva diagnóstico accionable y no altera stock ni saldo incorrectamente.
- El usuario puede seleccionar empresa/PV autorizado y nunca usar certificados de otra empresa.
- Una consulta CUIT completa datos y registra fecha, fuente y usuario.
- La cotización del dólar se sincroniza, queda auditada y puede aplicarse a un documento.
- POS muestra contexto fiscal correcto y su cierre concilia medios de pago.
- Remitos e inventario respetan las reglas de egreso.
- Reportes fiscales reproducen totales por entidad y consolidado autorizado.
- Backup y restore se prueban en un entorno limpio.

## 10. Fases sugeridas
1. Discovery y matriz de paridad Odoo 20 CE/Dolibarr.
2. Fundación multiempresa, seguridad y modelo argentino.
3. ARCA/WSAA/WSFEv1 y documentos fiscales.
4. Padrón y cotizaciones.
5. POS, pagos, Mercado Pago y cajas.
6. Compras, ventas, stock y remitos.
7. Reportes, importaciones y migración.
8. Hardening, pruebas integrales, documentación y producción.

## 11. Riesgos y decisiones pendientes
- Cambios normativos ARCA y disponibilidad de servicios.
- Licencias y compatibilidad de componentes reutilizados.
- Alcance exacto de “paridad Odoo 20 CE” según versión, addons CE instalados y addons propios necesarios.
- Proveedor autorizado para cotización del dólar.
- Estrategia multiempresa nativa de Odoo versus aislamiento por permisos, compañías y reglas de registro.
- Datos históricos y documentos que deben ser legalmente reproducibles.

## 12. Evidencia de referencia
- `/root/dolibarr/README.md`
- `/root/dolibarr/IMPLEMENTATION_STATUS.md`
- `/root/dolibarr/docs/ARCA.md`
- `/root/dolibarr/docs/MULTICOMPANY.md`
- `/root/dolibarr/custom/arcaargentina/`
- `/root/dolibarr/mercadopago/`
- `/root/dolibarr/cloverbridge/`
