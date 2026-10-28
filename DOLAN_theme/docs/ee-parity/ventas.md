# Paridad: Ventas EE (Cotizaciones) vs CE `sale_management`

Evidencia: `docs/evidence/ee-demo/full/ventas.png`. Módulo CE instalado (`sale_management` = installed desde F0/lote).

## EE observado
- Menús: Ventas · Órdenes / Productos / Reportes / Configuración.
- KPI strip: **Por confirmar · Por entregar · Por facturar** (colores) + widget
  derecha "Últimos 7 días → Órdenes de venta / Sales Revenue".
- Lista: Número, Fecha de la orden, **Entrega prometida**, Cliente, Total,
  Estado (Cotización / Orden de venta / Cancelado), **Estado de la factura**
  (Oportunidad de venta adicional / Por facturar / Facturado por completo /
  Nada que facturar), Actividades.
- Filtro "Mis cotizaciones"; onboarding con video (pagos en línea, firmas).

## CE vs gaps
- Estados de cotización/orden, entrega prometida y facturación = **nativo CE** ✓.
- **Gaps v3 candidatos** (si pedís DOLAN_ventas): KPI strip + widget 7 días,
  columna Estado de la factura, pagos en línea/firmas = EE (fuera de alcance).

Veredicto: **alto** (sólo KPIs/columna/onboarding faltan).
