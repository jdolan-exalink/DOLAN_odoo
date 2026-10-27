# Política de versiones y soporte — DOLAN_theme

## Matriz oficial

| Odoo | DOLAN_theme | Estado de soporte | Notas de evidencia |
|---|---|---|---|
| 20.0-20261015 CE (tag `odoo:20.0`) | `20.0.x.y.z` (semver interno: versión = serie Odoo + 4 segmentos) | **Certificado (v1, en construcción)** | única versión verificada en el entorno; auditoría en `research.md` |
| 19.x | — | **No soportado** | no existe línea 19; no se migran addons 19 (evidencia `web_responsive` → pantalla blanca) |
| 21.x / posterior | — | No disponible → no prometido | certificar al llegar: nuevo lote de adaptadores `compat/` + CI + matriz |

## Reglas

1. El manifest usa versión `20.0.<feat>.<fix>` mientras la serie certificada sea 20.0 (el runtime marca `installable=False` si la serie no coincide — verificado en `check_version`).
2. Ramas: `main` = serie activa certificada; `21.0` se crea al certificar 21; nada de ramas por versiones no disponibles.
3. Cada salto de serie mayor exige: actualizar `compat/`, recorrer checklist Owl, correr CI + tours + capturas Playwright, actualizar `odoo20-compatibility.md` y `ce-coverage-matrix.md`.
4. Detección de cambios: al actualizar Odoo, comparar puntos de extensión usados (vistas heredadas, registries, rutas, assets) contra la release nueva y documentar incompatibilidades en `research.md` (sección delta).
5. Sin `if version.startswith` como arquitectura: feature-detect solo en `compat/` y siempre documentado.
6. CI (deseado en Fase 5): lint + instalación/actualización/desinstalación por versión soportada + tours + capturas de referencia.

## Cadena de versiones de dependencias

| Dependencia | Pin |
|---|---|
| Imagen Odoo | `odoo:20.0` (release 20.0-20261015) |
| PostgreSQL | imagen `postgres:17` del stack |
| OCA interfaz | solo ramas `20.0` (hoy: `web_environment_ribbon`, `web_m2x_options` — evaluación pendiente; `web_responsive` ausente) |
| Playwright | a instalar con tag de versión fijado (bloqueo abierto) |
