# DOLAN_theme — Riesgos y mitigaciones

Actualizado: 2026-10-27 · Severidad: 🔴 alta / 🟠 media / 🟡 baja

| # | Riesgo | Sev. | Evidencia real | Mitigación |
|---|---|---|---|---|
| R1 | Cambios de API Owl3 rompen el cliente (pantalla blanca) | 🔴 | 6 rondas reales en esta sesión: `static props`, `useState`, `state` pelado, `t-esc`, `tree` | Checklist obligatorio en `odoo20-compatibility.md`; pruebas **en navegador** obligatorias por iteración; nada de "compila = funciona" |
| R2 | Patch de componentes core = regresión global al actualizar | 🔴 | `web_responsive` 19.0 rompió TODA la UI en 20 | Preferir herencia de vistas/assets/CSS; parches OWL solo con prueba + registro en matriz; instalaciones de terceros solo de rama 20.0 |
| R3 | Mejoras visuales ocultan campos/validaciones → brecha de seguridad | 🔴 | principio no negociable del mandate | Review explícito: nunca `display:none` sobre campos requeridos, mensajes de validación o alerts; checklist de QA de formularios |
| R4 | Multiempresa/ACL respetada por widgets de Home | 🔴 | widgets deben usar el contexto del usuario | Solo ORM con contexto; tests con2 empresas y roles distintos (empleado vs manager) |
| R5 | POS (táctil) roto por estilos globales | 🟠 | POS instalado en el stack; UI táctil propia | Assets del tema fuera de POS; smoke test dedicado; mejoras POS solo por extensión con pruebas |
| R6 | Editor Website / front público afectado | 🟠 | `website` es app CE instalable | Scope a backend (`web`); decisión de front público aparte y aprobada |
| R7 | Degradación de rendimiento (assets grandes, patches en hot path) | 🟠 | bundle actual ~8,3 MB JS | Medir con/Antes-Después; tokens en CSS; JS mínimo; sin writes por render; capturas de métricas |
| R8 | Playwright no instalado (QA browser bloqueado) | 🟠 | verificado: `playwright` ausente | Instalar con aprobación en setup de Fase 2; si falla el despliegue → documentar y pedir autorización (no sustituir versión de Odoo) |
| R9 | Terceros asumen compatibilidad de addons 19.x | 🟠 | `web_responsive` real | Política: solo ramas 20.0; matriz de soporte pública en docs |
| R10 | Tema acoplado a vertical Dolan/IA futura | 🟠 | mandate | Estructura genérica desde el día1; identidad = marca visual, no lógica de negocio; sin referencias a AR/LLM dentro del addon |
| R11 | Actualizaciones de Odoo rompen vistas heredadas | 🟡 | nombres de vistas/registros cambian entre versiones | Herencias con `inherit_id` + xpath mínimos; CI de instalación/upgrade; matriz de cobertura con evidencia |
| R12 | Modo oscuro con contraste insuficiente (a11y) | 🟡 | — | Tokens semánticos + chequeo de contraste en QA (herramienta/manual) |
| R13 | Densidad compacta rompe legibilidad/touch | 🟡 | — | Límites mínimos de tamaño de fuente y targets; pruebas de usabilidad con usuarios reales en Fase 2 |
| R14 | Confundir "ocultar" con "seguro" en listas | 🟡 | R3 | Columnas ocultas = preferencia de usuario, nunca eliminación de datos ni permisos |
| R15 | Datos de prueba vs producción | 🟡 | stack `dolan` es productivo | Dev DB separada (`theme_dev`, con demo); nunca tocar `dolan`; backups ya existentes en `backups/` |

## Riesgos de vertical (contexto del stack actual)

- **Contabilidad AR (l10n_ar + fiscal_ws)**: formularios de diario/movimiento con campos latam — herencias deben preservar QR/CAE/validaciones.
- **MRP / Inventario**: kanbans y rutas densas → probar con datos grandes (rendimiento de listas).
- **Compras/Ventas**: wizards (descuentos, pagos) y chatter → checklist de diálogos.
- **POS**: ver R5.

## Bloqueos abiertos (requieren decisión)

1. **Playwright** no instalado → pedir autorización de instalación al iniciar Fase 2.
2. **Dirección visual** (3 prototipos) → aprobación requerida antes de Fase 3.
3. **Datos ficticios** para dev: crear DB `theme_dev` con demo (decisión de arranque de Fase 2/3; no se toca `dolan`).
