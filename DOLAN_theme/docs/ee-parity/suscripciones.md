# Parity: Suscripciones (EE) vs DOLAN_suscripciones v1

Evidencia EE: `docs/evidence/ee-demo/full/suscripciones.png` (lista + onboarding).

## EE observado
- Menús: Suscripciones · Suscripciones / Productos / Reportes / Configuración.
- Lista: Número, Cliente, **Siguiente** (fecha ↑), **Vendedor**, **Actividades**
  (chatter), **Recurrente** (importe), **Plan recurrente**, **Estado de la
  suscripción** (badges: *Venta adicional, Cotización, Renovado, En pausa…*).
- Filtro guardado "En progreso o En pausa"; selectores de vista (lista,
  calendario, gráfico, pivot, etc.).
- Onboarding: MRR + churn + CLTV ("Automatizar facturas y pagos…").

## Nuestro v1 (`DOLAN_suscripciones`)
- plan (nombre, precio, ciclo_dias, producto) · suscripción (cliente, plan,
  fecha_inicio, fecha_ultima, próxima, estados activa/pausada/cancelada).
- **Cron diario** → factura en borrador por período vencido + avance de fecha.

## Gaps → v2 (orden sugerido)
1. **Estados de negocio**: fase de venta (Cotización/Renovado/Venta adicional)
   además del ciclo activo/pausada/cancelada.
2. **Vendedor + actividades** en lista (Campo `user_id` + activity_ids).
3. **Vista calendario + gráfico de recurrente** (lista alternativa).
4. **MRR / métricas** en página tipo KPI (patrón de nuestros tableros).
5. Cobro automático (EE) vs nuestros borradores → fuera de alcance AR
   (transferencias/CAE); documentado como diferencia deliberada.

Veredicto: **parcial** — núcleo funcional (recurrencia + facturación) cubierto;
falta capa comercial/métricas.
