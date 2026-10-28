# Paridad: Contabilidad EE (Tablero) vs DOLAN_contabilidad + dolan_dash

Evidencia: `docs/evidence/ee-demo/full/contabilidad.png` (+ `ee-demo/01-dashboard-facturacion.png`).

## EE observado
- KPI superiores: Facturas, Gastos, Efectivo, Por cobrar, Por pagar (+ tile
  "Configura el diseño de tu factura").
- Paneles onboarding: Ventas Preimpreso (pasos electrónica), **Compras IA**
  (arrastrar/soltar), **Banco 26.000 bancos** (agregación EE/IAP), Cheques de
  Terceros/Rechazados (gráficos), **Declaración fiscal** (períodos, plan de
  cuentas, fecha 07/11/2026).

## Nuestros equivalentes
- `dolan_dash` KPIs: Facturas, Gastos, Efectivo, Por cobrar, Por pagar
  (orden EE) → **paridad directa de la tira de KPI** (L16).
- `DOLAN_contabilidad`: emitidas/recibidas + IVA débito/crédito/liquidado
  del mes (además del EE).
- Electrónica ARCA: **más allá del EE** (fiscal_ws propio, L de migración).

## Gaps
1. **Declaración fiscal** con períodos/checklist → candidato v2 (AR: períodos
   IVA/CAE; usar modelo propio, sin IAP).
2. Onboarding "Banco 26k" = EE/IAP → ya documentado como brecha (L18).
3. Cheques de Terceros → cerrado por datos (0 uso en origen).
4. Arrastrar/soltar IA en Compras → nuestro `DOLAN_ai` + plantilla P3 (v2:
   adjuntar imagen → OCR vía ChatGPT, cuando se retome F4-OCR).

Veredicto: **parcial-alto** — KPI y fiscal AR cubiertos; onboarding/banco EE
quedan como brechas conocidas.
