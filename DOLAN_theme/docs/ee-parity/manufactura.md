# Paridad: Manufactura EE (Órdenes de fabricación) vs CE `mrp`

Evidencia: `docs/evidence/ee-demo/full/manufactura.png`. `mrp` instalado desde F0.

## EE observado
- Menús: Manufactura · Operaciones / Productos / Reportes / Configuración.
- Lista Órdenes de fabricación (filtro "Por hacer"): Referencia, **Inicio**
  (ventanas relativas), Producto, **Siguiente actividad**, Origen,
  Estado del componente, Cantidad, Estado (Borrador/Confirmada/Por
  cerrar/Hecho/Cancelada) + prioridad (estrella).
- Onboarding educativo (BOM ejemplo mesa).

## CE vs gaps
- Órdenes, estados, BOM, cantidades, prioridad = **nativo CE** ✓.
- **Gaps**: "Siguiente actividad" (punto de entrada a work-orders →
  depende de `DOLAN_taller`, EE-only `mrp_workorder`), y cualquier panel KPI.

Veredicto: **alto** (lista/estados cubiertos; detalle operativo atado a DOLAN_taller).
