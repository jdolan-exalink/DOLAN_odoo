# Migración Dolibarr → Odoo 20 (DB `dolan`)

Procedimiento reproducible de la migración del histórico de Dolibarr
(`/root/dolibarr`, Dolibarr 23.0.3 + MariaDB) al stack
`/root/odoo20/odoo20-argentina` (Odoo 20 CE + localización AR), DB **`dolan**.

## Decisions (user, 2026-10-26)

- 3 empresas multi-CUIT: DOLAN SS (RI, CUIT 30719030358, PV1), JUAN MARTIN
  DOLAN (Mono, 20266946008, PV8), CINTIA VERONICA GOROSITO (Mono,
  27345636388, PV4) — cada una con SU histórico (Dolibarr entities 1/2/3).
- Todo cerrado/pagado: todas las facturas se importan `posted` + `paid`
  (sin cuentas por cobrar abiertas), aunque Dolibarr las tenga validadas.

## Pipeline (orden)

1. **Extract** — `extract.sh`
   - Solo lectura sobre `dolibarr_mariadb` (credenciales desde
     `/root/dolibarr/.env`, nunca impresas).
   - JSON server-side (`JSON_ARRAYAGG`) en chunks de 200 filas con
     `JSON_VALID` por chunk. Gotchas resueltas: `geopoint` tiene bytes
     inválidos que rompen el serializador JSON del server (columna
     excluida); agregados ~1MB rompen (`JSON_VALID=0`); TSV directo rompe
     con newlines embebidos.
   - Salida: `data/*.json` + `manifest.json` (conteos de reconciliación:
     societes 2394, facturas 189, líneas 226, productos 295, pagos 13).
2. **Empresas** — `create_companies.py` + `fix_company_resp2.py`
   - `account.chart.template.try_loading('ar_ri', co)` por empresa; CUIT y
     responsabilidad post-fix (el chart pisaba la responsabilidad).
   - Resp: `l10n_ar.res_IVARI` (RI), `l10n_ar.res_RM` (Mono).
3. **Terceros** — `import_partners.py` → `partner_map.json`
   - CUIT en `llx_societe.siren` (dígitos); responsabilidad en
     `llx_societe_extrafields.condicion_iva` (RI/MO). Teléfono único en
     Odoo 20: `phone` (mobile-first).
4. **Productos** — `import_products.py` → `product_map.json`
   - IVA de producto por `tva_tx` (21/10.5) buscando `account.tax` por
     empresa.
5. **Facturas/NC/depositos** — `import_invoices.py` → `invoice_map.json`
   - `move_type` por familia ARCA del tipo documental (`doc.internal_type`):
     los códigos ARCA 3/8/13 son NC → `out_refund` (Dolibarr v23 usa
     type 1 y 2 para NC; 3 NC vienen con totales negativos → se importan
     en valor absoluto, estándar de Odoo).
   - **IVA por línea = `total_tva/total_ht` de la fuente** (redondeado a
     la tasa configurada): `tva_tx` es inconsistente en el origen (declara
     21 donde el total es 10.5%; mono declara 21 con total_tva=0 → sin
     IVA). `price` nulo con `total_ht>0` → unidad derivada
     `total_ht/qty/(1-desc)`.
   - Journals SIN `l10n_ar_fiscal_ws` → el `_post` de fiscal_ws no toca
     nada (los CAE reales se escriben después del post:
     `l10n_ar_fiscal_auth_code(_due)`, `auth_mode=CAE`, `result=A`).
   - Pago total por `account.payment.register` (journal bank de la
     empresa) ⇒ `payment_state=paid`.
   - Numeración oficial latam: `name` = `ref` de origen (formato
     `FA-A 00001-00000001` = `doc_code_prefix` + PV 5 dígitos + NUM 8);
     `l10n_latam_document_number` se deriva del name. Los prefijos del
     origin coinciden 1:1 con `doc_code_prefix` de Odoo (1→FA-A, 3→NC-A,
     6→FA-B, 8→NC-B, 11→FA-C, 13→NC-C); la serie ARCA por tipo evita la
     unicidad (name, journal).
   - Resumible: mapa cada 20; repair loop `repair_delete.py`
     (reconcile→pagos→draft→unlink, `REPAIR_LIMIT` para probar de a uno).
6. **Validación** — `validate.py`
   - 189/189 en mapa; posted+paid 189; 177 out_invoice + 12 out_refund;
     54/48/87 por empresa; CAE 100% igual al origen; totales ±0.02 → 0
     desvíos; name/docnum oficiales → 0 desvíados.

## Datos sincronizados al container

`docker cp migration/data odoo20-argentina_odoo:/tmp/migration` (ojo: si el
destino existe, crea `/tmp/migration/data`). Los mapas viven en `/tmp/*.json`
del container (el usuario odoo no puede escribir en `/tmp/migration/data`,
que queda root).

## Remitos (S7) y branding (S9)

- `import_remitos.py` (`REMITO_LIMIT` para prueba de a uno): 11
  expeditions de Dolibarr → stock.picking en DOLAN SS con name == ref
  (REM/IN → incoming), state done, `date_done` = date_expedition, lineas
  de texto en `description_picking(_manual)` + `note` via producto
  sintetico consu `REMITO-IMPORT`. Requisitos Odoo 20: modulo `stock`
  instalado en dolan; warehouses creados a mano para companies 5/6/7
  (`create_missing_warehouse` solo cubre la primera); move sin campo
  `name` y `company_id` explicito (defaulta a la company del usuario).
- Numeracion futura (S9): verificada por simulacion — las series
  continuan solas por tipo documental (FA-A→44, FA-B→8, FA-C→44/181,
  NC→n+1) sin configuracion extra; PVs por journal ya correctos (1/8/4).
- `apply_branding.py`: logo (logowebDOLANSS.png, comun a las 3 entities)
  en `logo`/`logo_web` + cabecera (Lavalle 4242, Santa Fe 3000, tel,
  email, web) en el partner de cada empresa. Odoo 20: binarios aceptan
  base64-str o `BinaryValue`.

## Re-ejecución

Los scripts son idempotentes vía mapas (`skip_existente`); borrar un move
excluido del mapa hace que el importador lo recree. `validate.py` siempre
debe cerrar en cero antes de tocar nada más.

## Fase go-live (noviembre 2026)

- **Certificados ARCA** (`install_certs.py`): alias+certificado por company
  (type=production, mapeo por CUIT del subject; DOLANSS vence 2027-07,
  DOLAN2026/GOROSITO2026 vence 2028-10). Diarios venta con
  `l10n_ar_afip_pos_system=RAW_MAW` (SQL: el guard de l10n_ar bloquea el
  cambio con facturas validadas) -> `l10n_ar_fiscal_ws_id=wsfe` + PV 1/8/4.
  WSAA producción validado (tickets de 12h con token+sign). El parámetro
  `l10n_ar_fiscal_ws.env_type` queda en **homologation** (fallback local)
  hasta el arranque: al iniciar el mes setear `production` y emitir.
- **Mis Comprobantes** (`import_bills.py`, `BILL_LIMIT` para piloto):
  6 bills reales importados (suma 3.607.964,75 == fuente, not_paid fiel) y
  6 placeholders (PROVx) excluidos. Gotchas: IVA de det de compras en
  columna `tva`; RI exige UN impuesto grupo VAT por linea y en cero usa
  "VAT Not Applicable"; mapa saneado contra DB al inicio (ids fantasma
  tras rollback).
- **Backup** (`backup-dolan.sh`): pg_dump gzip diario + configs, retención
  30d / 12 mensuales. Cron sugerido (no autoinstalado):
  `0 2 * * * cd /root/odoo20/odoo20-argentina && ./backup-dolan.sh >> backups/backup.log 2>&1`
- **Cobranzas**: journals bank con outstanding accounts asignados
  (2/2 method lines x3 empresas, metodo oficial del chart ar_ri). Flujo:
  registrar pago -> reconcilia contra outstanding -> conciliar extracto.
- **Dashboard**: módulo `dolan_dash` (menú Operaciones → Tablero) con
  Facturas (pivot por mes/empresa), NC, Remitos y Compras/por pagar.
- **POS**: instalado, sin configurar (fuera de alcance por decisión).

---

## Cargar compras nuevas (CSV)

Plantilla: [`compras_plantilla.csv`](compras_plantilla.csv) — 14 columnas con
**rutas canónicas de Odoo** (así las reconoce el importador nativo sin
mapear a mano), con una fila de ejemplo extraída de una factura real ya
importada.

| Columna | Contenido |
|---|---|
| `move_type` | siempre `in_invoice` |
| `name` | comprobante (ej.: `LI-A 01019-00057174`) |
| `partner_id` | proveedor por nombre (debe existir en Contactos) |
| `invoice_date`, `ref` | fecha del comprobante, número interno |
| `l10n_latam_document_type_id` | **nombre del tipo sin el código** (ej.: `LIQUIDACIONES A`, no `(63) LIQUIDACIONES A`) |
| `l10n_latam_document_number` | punto de venta - número |
| `journal_id` | diario (ej.: `Compras`) |
| `line_ids/*` | producto, descripción, cantidad, precio, impuestos (`IVA 21%`), cuenta |

**Flujo**

1. Compras → Facturas de compra → **Importar** → subir el CSV.
2. Las columnas se mapean solas (los encabezados *son* las rutas).
3. **Probar importación** (dry-run: valida sin escribir) → **Importar**.
4. Avisos ("varias coincidencias") no bloquean; si una columna es ambigua en
   multi-compañía, trabajar con la **compañía destino activa** (el importador
   resuelve nombres dentro de las compañías del usuario activo; cruzar
   empresas da el error *"Hay inconsistencias en la empresa"*).

**Multi-línea:** una fila por línea de factura; deje las columnas del
comprobante vacías en las filas continuación (igual que exporta Odoo) y el
importador las agrupa en el mismo comprobante.

**Validación ejecutada (2026-10-27, odoo shell):** dry-run `SIN ERRORES`;
import real 6→7 facturas con `ids: [754]`; `env.cr.rollback()` restauró 6
(sin persistir). Ver `odd/tasks/dolan-theme.md` L17.
