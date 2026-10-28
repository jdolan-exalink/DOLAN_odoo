# Paridad: Taller EE → ¿módulo CE nativo?

Evidencia: `docs/evidence/ee-demo/full/taller.png` (onboarding "Active sus
centros de trabajo"; etiquetas: Seleccionar operador, Registrar materiales,
Bucle de retroalimentación, Temporizador, **Control de calidad**).

## Análisis
- La pantalla EE = **tablet UI de centros de trabajo / work orders** (no un
  modelo nuevo). Verificar equivalencia CE: `mrp_workorder` (+ worksheet,
  barcode) en la imagen local (estado en `ir_module_module` — ver Log L23).
- "Control de calidad" en el flujo del taller → nuestro `DOLAN_calidad`
  encaja como capa de puntos de control sobre operaciones.

## Plan
1. Si `mrp_workorder` existe en CE → **activarlo** (lote siguiente) y solo
   faltaría pulir estética → gap EE ≈ cubierto sin código.
2. Si no existe → candidato `DOLAN_taller` (work-center UI propia), prioridad
   post-F5.

Veredicto: **pendiente de estado del módulo** (ver L23); no construir nada
hasta confirmar.
