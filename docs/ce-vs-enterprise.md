# Odoo 20 CE vs Enterprise — barcode y contabilidad Argentina

Tabla de diferencias funcionales entre Odoo 20 Community Edition (CE) y Odoo 20
Enterprise (ET), con el reemplazo community recomendado por área. Solo se
compara funcionalidad: el código de Enterprise es propietario (licencia OPL-1)
y no se copia, porta ni decompila.

Fuentes verificadas (octubre 2026):

- Repo público `odoo/odoo` branch `20.0` (addons CE).
- `ingadhoc/*` branches `20.0` (localización Argentina community).
- `OCA/*` branches `20.0` (migración OCA a 20.0 recién empezada: la mayoría de
  los repos todavía no tiene módulos migrados).

## 1. Código de barras

| Capacidad | Odoo 20 CE | Odoo 20 Enterprise | Reemplazo community en este setup |
|---|---|---|---|
| Escaneo en campos de formularios (picking, producto, ubicación) | ✅ core `barcodes` | ✅ (incluye lo de CE) | Core CE: se instala con Inventario/Ventas |
| Nomenclaturas GS1-128 (parsear lote, vencimiento, GTIN, cantidades) | ✅ core `barcodes_gs1_nomenclature` | ✅ | Core CE |
| Campo código de barras en producto / variantes / empaques | ✅ core | ✅ | Core CE |
| UI de escaneo full-screen para recepción, entrega, transferencias e inventario (`stock_barcode`) | ❌ | ✅ `stock_barcode`, `stock_barcode_mrp`, `stock_barcode_quality` | ⚠️ Sin equivalente OCA migrado a 20.0 todavía. Flujos posibles en CE: escaneo en el form del picking vía `barcodes`, terminal móvil con la UI estándar de Odoo, o desarrollo propio |
| Generación automática de códigos (EAN13 desde secuencia, etc.) | ❌ | ❌ (tampoco en ET) | OCA `barcodes_generator_*` (repos `product-attribute` / `stock-logistics-barcode`): hasta 19.0; migración 20.0 pendiente |
| Etiquetas / impresión de códigos de barras | ✅ reportes QWeb con `barcode` widget | ✅ | Core CE (reportes con widget barcode); OCA `print` para etiquetas si hace falta |
| Escaneo en órdenes de venta (líneas por lectura) | ❌ (solo en picking/inventario) | ✅ dentro de `sale_barcode` | ✅ `sale_barcode` de `ingadhoc/sale` (verificado instalable en 20.0) |
| Price checker (consulta de precio por escaneo) | ❌ | ❌ | ✅ `sale_price_checker` de `ingadhoc/sale` (verificado instalable en 20.0) |

Conclusión: en CE 20 se pierde principalmente la app de escaneo móvil
(`stock_barcode`). Para recepción/remito se puede operar con escáner USB/HTTP
sobre los formularios estándar (el módulo `barcodes` core enfoca el campo y
procesa la lectura), y `barcodes_gs1_nomenclature` cubre etiquetas GS1. La UI
touch dedicada queda como gap documentado.

## 2. Contabilidad y localización Argentina

| Módulo / capacidad | Odoo 20 CE | Odoo 20 Enterprise | Reemplazo community en este setup |
|---|---|---|---|
| Plan de cuentas AR, impuestos, tipos de comprobante AFIP, percepciones base, monotributo (`l10n_ar`) | ✅ core CE | ✅ | Core CE |
| Retenciones AR (`l10n_ar_withholding`) | ✅ core CE (paso a comunidad en 20) | ✅ | Core CE |
| POS con régimen fiscal AR (`l10n_ar_pos`) | ✅ core CE | ✅ | Core CE |
| Remitos AR (`l10n_ar_stock`) | ✅ core CE | ✅ | Core CE |
| Facturación electrónica AFIP/ARCA WSFEv1 + WSAA (`l10n_ar_edi`) | ❌ | ✅ (usa infraestructura de conexión de Odoo) | ✅ `l10n_ar_fiscal_ws` de `ingadhoc/odoo-argentina-ce`: port 20.0 de ADHOC habilitado y validado en nuestro stack (installable habilitado por el script; suite 38/38 en verde, 2026-10-26). Incluye WSAA (LoginCms), wsfe, wsbfe, wsfex, wsfecred y padrón A5 |
| Retenciones/percepciones avanzadas por jurisdicción, regs. provinciales | ✅ core `l10n_ar_withholding` (verificado instalado en 20) | ✅ módulos ET dedicados | `l10n_ar_tax*` de `ingadhoc/odoo-argentina`: `installable: False` en 20.0 (WIP). Evaluar solapamiento con `l10n_ar_withholding` core cuando migre |
| Compras AR, bancos AR, UX de flujos | ❌ / parcial | ✅ | `l10n_ar_purchase` y `l10n_ar_ux` ✅ instalables en 20.0 (verificado); `l10n_ar_bank` y `account_payment_pro` ❌ `installable: False` (WIP) |
| Ventas AR: tipos de comprobante en ventas, preimpresos, remitos de venta | parcial | ✅ | ⚠️ `l10n_ar_sale*`, `l10n_ar_preprinted_template`, `l10n_ar_stock_*` y `sale_ux`: todos `installable: False` en 20.0 (WIP). `l10n_ar_stock` core CE sí disponible |
| Libros IVA digital / reportes fiscales AFIP (`l10n_ar_reports`) | ❌ (verificar alcance en instancia) | ✅ | `ingadhoc/argentina-reporting` (aún sin branch 20.0 publicada — gap temporal) |
| Factura de crédito electrónica MiPyME (QR ARCA) | parcial (QR en core) | ✅ integrado | pyafipws + `l10n_ar_fiscal_ws` cubren la emisión; QR core |

Conclusión: con el core CE 20 + los módulos ingadhoc 20.0 instalables hoy, la
cobertura contable AR es funcional pero incompleta: falta la facturación
electrónica (ver §2.1). La conexión AFIP con pyafipws es distinta en
arquitectura (directa con certificados propios vs el servicio de Odoo), lo que
en community es además una ventaja: no depende de IAP de Odoo.

## 2.1 Estado verificado de la migración ingadhoc a 20.0 (2026-10-26)

Odoo 20 es recién liberado (imagen 20.0-20261015). Instalación headless
verificada sobre `argentina_test` (Odoo 20 + postgres:17):

✅ **Instalados y funcionando**: `l10n_ar` (core: plan de cuentas AR con 50
cuentas, tipos de responsabilidad AFIP), `l10n_ar_purchase`, `l10n_ar_ux`,
`account_internal_transfer`, y otros 16 módulos ingadhoc compatibles
(`account_ux`, `pos_ux`, `sale_order_type_ux`, etc.).

❌ **Aún no instalables en 20.0** (`installable: False`, migración WIP en
ingadhoc): `l10n_ar_tax`, `l10n_ar_bank`, `l10n_ar_sale`,
`l10n_ar_preprinted_template`, `sale_ux`, `account_payment_pro`,
`l10n_ar_fiscal_ws_reports`.

✅ **`l10n_ar_fiscal_ws` validado en nuestro stack** (2026-10-26): el port
20.0 de ADHOC (v20.0.1.0.0) habilitado con installable:True instala limpio
y su suite de tests pasa 38/38 en verde sobre `argentina_test`. El entorno
resuelve homologación por defecto (parámetro `l10n_ar_fiscal_ws.env_type`);
sin certificados en homologación la facturación es local (código de
autorización local + QR), que es el comportamiento testeado por el módulo.
Artefacto upstream a vigilar: los tests de CAE hacen `cr.commit()` dentro de
`_l10n_ar_post_batch`, lo que puede persistir `env_type=production` entre
corridas de suite (higiene de test del módulo, no del stack).

Rutas restantes mientras la migración madura: (a) esperar el release de
ingadhoc; (b) base Odoo 19.0, donde todo está maduro; (c) port propio
adicional de los módulos WIP que hagan falta. La tabla se actualizará con
cada release.

## 3. Cómo actualizar esta tabla

Al migrar OCA o publicar nuevos branches ingadhoc para 20.0, actualizar las
filas marcadas ⚠️/gap y volver a verificar con:

```bash
./crear_odoo20.sh --check          # conectividad de repos 20.0
npx -y rea-agents@6.8.0 doctor --client pi --json   # estado del entorno de análisis
```
