# Cumplimiento vs `ingadhoc/odoo-argentina`

> S10 (user: "te paso un repo para que verifiques como lo hacen y si cumplimos todo").
> Fecha 2026-10-31 · ramas analizadas: **19.0** y **staging.20.0** (clones locales en `/tmp/adoa`, `/tmp/adoa20`).

## 1. Qué hace ese repo
Es la localización Argentina de ADHOC para Odoo CE: **9 módulos** — UX contable AR, bancos AR, compras AR y la familia de **retenciones/percepciones automáticas** (`l10n_ar_tax*`). **No** incluye facturación electrónica (esa vive en `ingadhoc/odoo-argentina-ce`: `l10n_ar_fiscal_ws`, que nosotros portamos nosotros mismos).

## 2. Matriz de cumplimiento (ellos → nosotros)

| Módulo | 19.0 | staging.20.0 | Nuestro estado | Cumplimiento |
|---|---|---|---|---|
| `l10n_ar_ux` (UX contable AR) | 19.0.1.14 | **20.0.1.0.0** | instalado **20.0.1.0.0** | ✅ **cumple** |
| `l10n_ar_purchase` (compras AR) | 19.0.1.3 | **20.0.1.0.0** | instalado **20.0.1.0.0** | ✅ **cumple** |
| `l10n_ar_purchase_stock` (compras↔stock) | 19.0.1.1 | **20.0.1.0.0** | **instalado hoy** (20.0.1.0.0) | ✅ **cumple** (cerrado en este pase) |
| `l10n_ar_bank` (bancos AR) | 19.0.1.1 | 20.0.1.0.0 **pero depende de `base_bank`, que no existe en Odoo 20** | no instalable | ⛔ **bloqueo upstream** |
| `l10n_ar_tax` (retenciones/percepciones automáticas) | 19.0.1.37 ✅ | **19.0.1.35 `installable=False`** (WIP) | no instalado | ⛔ **bloqueo upstream** |
| `l10n_ar_tax_backward_compatibility` | 19.0 | WIP | no instalado | ⛔ upstream |
| `l10n_ar_tax_neuquen` (mínimo IIBB) | 19.0 | WIP | no instalado | ⛔ upstream |
| `l10n_ar_tax_payment_method` | 19.0 | WIP | no instalado | ⛔ upstream |
| `l10n_ar_tax_python` (fórmulas en posiciones fiscales) | 19.0 | WIP | no instalado | ⛔ upstream |

**Resumen: 3/9 cumplidos, 6/9 bloqueados por el propio upstream** (5 por `l10n_ar_tax*` sin migrar y 1 por `base_bank` inexistente en Odoo 20).

## 3. Extras que tenemos nosotros (no están en ese repo)
- `l10n_ar_fiscal_ws` + `l10n_ar_fiscal_ws_reports` → **port propio** de `odoo-argentina-ce` (WSAA/WSFE/WSMTXCA/WSCT, Libro de IVA, Análisis de IVA).
- `l10n_ar_pos`, `l10n_ar_stock`, cheques (`l10n_latam_check` core) + cheques rechazados propios.
- IIBB por jurisdicción (core `l10n_ar`) y consulta de comprobantes en ARCA.
- **15 módulos propios**: DOLAN_theme, DOLAN_ai, DOLAN_contabilidad, DOLAN_whatsapp, dolan_dash, dolan_ui, DOLAN_declaracion, DOLAN_bancos, DOLAN_calidad, DOLAN_taller, DOLAN_alquileres, DOLAN_suscripciones, DOLAN_flotilla, DOLAN_mantenimiento, DOLAN_codigo_barras.
- OCA portados a 20.0: `report_xlsx`, `report_xlsx_helper`, `date_range`, `partner_statement`.

## 4. Bugs corregidos al verificar
1. **El installer clonaba `--branch 20.0` de `odoo-argentina`, rama que no existe** (su migración vive en `staging.20.0`) → un deploy nuevo quedaba sin esos módulos. Corregido con mapeo de rama en `crear_odoo20.sh`.
2. Nuestras copias de `l10n_ar_bank` y `l10n_ar_purchase_stock` eran **19.0** (parcheables): actualizadas a `staging.20.0`; `purchase_stock` **instalado y verificado**, `bank` no puede instalarse (dependencia `base_bank` inexistente en Odoo 20).

## 5. Acción recomendada
1. **Retenciones/percepciones** (`l10n_ar_tax*`): es la mayor brecha y la cubre la **Etapa 1 de `docs/propuesta-latam.md`** — o esperar a que ADHOC publique el 20.0 de staging, o portarlo nosotros (es el módulo grande de esa familia).
2. `l10n_ar_bank`: preguntar a ADHOC por el destino de `base_bank` en 20.0 o replicar la lista de bancos como datos propios (es sólo un catálogo).
3. Vigilar `staging.20.0` de ADHOC: cuando `l10n_ar_tax` salga de WIP, subirlo y re-ejecutar la instalación desde cero.
