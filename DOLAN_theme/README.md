# DOLAN_theme

Tema/UX moderno para **Odoo 20 Community Edition** — módulo independiente (sin Enterprise, sin editar core) para reducir la curva de aprendizaje con estética de espíritu Enterprise pero identidad propia. Genérico: sin verticales de negocio dentro del addon.

## Estado

| Fase | Estado |
|---|---|
| 0 — Auditoría técnica | ✅ completada (docs/) |
| 1 — Investigación (detallada) | 🔄 continúa con Fase 0 |
| 2 — UX/UI: sistema de diseño + 3 prototipos | ⏳ **espera aprobación de dirección visual** |
| 3–5 — MVP, UX avanzada, QA/cobertura CE | ⏳ posterior a aprobación |

## Lectura obligatoria

- `docs/research.md` — auditoría y evidencia del entorno Odoo 20.
- `docs/odoo20-compatibility.md` — matriz de soporte + checklist Owl 3.
- `docs/architecture.md` — estructura del addon y capas.
- `docs/risks.md` — riesgos, bloqueos abiertos.
- `docs/ce-module-inventory.md` · `docs/ce-coverage-matrix.md` · `docs/version-support-policy.md` — inventario/policy.
- `docs/prototypes/` — tres propuestas visuales navegables (HTML estático).

## Instalación (cuando exista el addon)

```bash
# copiar DOLAN_theme/ al addons_path e instalar desde Apps, o:
odoo-bin -i DOLAN_theme -d <db> --stop-after-init
```

Hoy **el addon todavía no existe**: Fase 0 solo entrega auditoría, arquitectura, riesgos y prototipos pendientes de aprobación.

## Licencia propuesta

LGPL-3 (compatible con CE y con futura propuesta OCA). Revisar lineamientos OCA antes de publicar.
