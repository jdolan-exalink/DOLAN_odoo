# Paridad: Código de barras (EE) vs DOLAN_codigo_barras v1

Evidencia EE: `docs/evidence/ee-demo/full/código-de-barras.png`.

## EE observado
- App dedicada a pantalla completa: "Lector de códigos de barras" con gráfico
  grande + **"Escanear o acercar"** y modos:
  - escanea **producto o embalaje** (localiza),
  - escanea **recolección** (abre transferencia),
  - escanea **contacto** (pendientes),
  - escanea **tipo de operación** (inicia),
  - botones de entrada: **Operaciones** / **Contar inventario**.

## Nuestro v1 (`DOLAN_codigo_barras`)
- Página con input autofocus (Enter): lookup por **barcode o SKU** →
  producto + **existencias por ubicación** (multi-compañía, sudo lectura).

## Gaps → v2
1. **Layout de escáner dedicado** (pantalla con gráfico + estados) — sólo
   cosmético sobre nuestro input actual.
2. **Semántica de escaneo ampliada**: códigos de *recolección/picking*,
   *contacto* y *tipo de operación* además de producto (resolver por prefijo
   o búsqueda global → acciones).
3. **Modos de entrada**: acceso rápido a Operaciones y Conteo de inventario.
4. Cámara/"acercar" (lector USB es el caso real en depósito; webcam = opcional).

Veredicto: **parcial** — lookup producto/stock cubierto y probado; faltan
flujos de escaneo operativos.
