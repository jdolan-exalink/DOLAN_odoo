# Paridad: Alquiler (EE) vs DOLAN_alquileres v1

Evidencia EE: `docs/evidence/ee-demo/full/alquiler.png` (Órdenes de alquiler).

## EE observado
- Menús: Alquiler · Órdenes / **Programar** / Productos / Reportes / Configuración.
- **KPI strip**: Hoy · Pickups · Returns · Tarde | Por confirmar · Por facturar.
- Lista: Referencia, Cliente, **Estado** (p.ej. Recolectada), **Fecha de
  recolección**, **Fecha de devolución**, Total, **Estado de la factura**
  (Por facturar / Facturado por completo / Oportunidad de venta adicional /
  Nada que facturar).
- Onboarding: **gantt de disponibilidad** por recurso (Printer/Projector),
  reservas con stock on-hand ("Reserved", "Pick up: Jan 28").

## Nuestro v1 (`DOLAN_alquileres`)
- contrato: cliente, bien, fecha_inicio/fin, tarifa_día, dias/total compute,
  estados borrador→activo→finalizado/cancelado, botón **Facturar** →
  `account.move` borrador (qty=días).

## Gaps → v2
1. **Pickup/Return** como fechas-hora separadas + estados de operación
   (Recolectada / Devuelta / Tarde) sobre el ciclo.
2. **KPI strip** (Hoy, Pickups, Returns, Tarde, Por confirmar, Por facturar)
   — patrón de tablero ya probado.
3. **Columna estado de factura** (Por facturar / Facturado / Nada…) en lista.
4. **Vista Programar (gantt)** de disponibilidad + reservas de stock
   (integración `stock` con producto alquilable).
5. Reportes (ocupación, ingresos por bien).

Veredicto: **parcial** — contrato/facturación base OK; faltan operaciones de
logística y planificación.
