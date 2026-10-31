# Propuesta Latam (Argentina) — siguiente etapa

> Contexto: S9 (user: "vamos con 4 5 6 y espero una propuesta latam?").
> Estado al 2026-10-31 · PRs #6..#13 mergeados · instalación desde cero verificada (EXIT=0, 97 módulos).

## 1. Ya desplegado (base sobre la que seguimos)
- **Facturación electrónica** WSFE / WSMTXCA / WSCT con WSAA en producción + homologación, CAE en los comprobantes.
- **Libro de IVA y Análisis de IVA** (`l10n_ar_fiscal_ws_reports`) e **IIBB por jurisdicción** (`l10n_ar`); **consulta de comprobantes en ARCA** desde Contabilidad.
- **Cheques de Terceros / Propios** (core `l10n_latam_check`) con tarjeta en el tablero y estados de cheque.
- **Estados de cuenta** (OCA `partner_statement`), **estados financieros propios** (Balance / Resultados / Flujo en XLSX) y **auditoría de diario propia** con controles (desbalanceados, borradores, huecos de secuencia).
- **WhatsApp (WAHA)**: envío con plantilla de comprobante (CAE + link), reintentos con backoff y estados de entrega.
- **Declaración Fiscal** (`DOLAN_declaracion`): períodos con checklist (IVA, ventas, compras, CAE pendientes).
- Backups diarios con prueba de restauración (fire-drill) + `shellcheck`/CI en PR.

## 2. Etapa 1 — corta, alto valor (1-2 sesiones)
1. **Retenciones y percepciones**: instalar `l10n_ar_withholding` (ya está en el repo, instalable) y exponer sus comprobantes/constancias en Facturación.
2. **Port de `l10n_latam_check_ux`** (bloqueo conocido, causa mapeada) → transferencias masivas de cheques, rechazos y reporte de cheques a fecha.
3. **Cierre fiscal asistido**: extender `DOLAN_declaracion` para validar Libro de IVA + IIBB + CAE pendientes **antes** de cerrar el período.

## 3. Etapa 2 — medios
4. **Estados financieros en PDF** además del XLSX (motor nativo `account.report` no trae visor en CE: o port OCA `account_financial_report` a 20.0 o generador QWeb propio).
5. **Libros digitales RG 1415** (ventas/compras): validación previa al upload de ARCA, con el mismo catálogo A4 ya aplicado.
6. **Percepciones IIBB/Ganancias** en facturación según el régimen del cliente (decisión de negocio).

## 4. Etapa 3 — decisiones tuyas
7. **OCR de facturas de compra** (diferido en L14) y **asistente IA con Claude/Ollama locales** → requieren proveedor/presupuesto.
8. **Restos Enterprise** (propios, nunca código OPL-1): cheques rechazados, archivos de trabajo, reporte anual.

## 5. Guardas
- Licencias: OCA = AGPL-3 (uso interno ok); **Enterprise = OPL-1 prohibido** (equivalentes propios LGPL).
- Todo port 19→20 se valida con instalación **desde cero** (`crear_odoo20.sh --deploy --init-db`, EXIT=0 / 97 módulos).
- QA: 8 suites Playwright + `shellcheck` en CI por PR (`.github/workflows/ci.yml`).
