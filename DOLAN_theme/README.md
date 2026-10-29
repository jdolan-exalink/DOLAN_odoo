# DOLAN_theme

Tema/UX moderno para **Odoo 20 Community Edition** — módulo independiente (sin Enterprise, sin editar core) para reducir la curva de aprendizaje con estética de espíritu Enterprise pero identidad propia. Genérico: sin verticales de negocio dentro del addon.

## Estado

El addon está implementado para Odoo 20 CE y verificado en la base de prueba `dolan`. La interfaz incluye navegación lateral, una grilla de aplicaciones, y modo claro/oscuro.

## Lectura obligatoria

- `docs/research.md` — auditoría y evidencia del entorno Odoo 20.
- `docs/odoo20-compatibility.md` — matriz de soporte + checklist Owl 3.
- `docs/architecture.md` — estructura del addon y capas.
- `docs/risks.md` — riesgos, bloqueos abiertos.
- `docs/ce-module-inventory.md` · `docs/ce-coverage-matrix.md` · `docs/version-support-policy.md` — inventario/policy.
- `docs/prototypes/` — tres propuestas visuales navegables (HTML estático).

## Uso e instalación

Con `DOLAN_theme` instalado:

- La grilla de aplicaciones está disponible desde el menú **Inicio** o en `/dolan_apps`.
- El botón 🌓 del systray alterna entre claro y oscuro. La preferencia se guarda en `localStorage` por navegador; si el almacenamiento no está disponible, el cambio dura hasta recargar.
- La grilla muestra iconos de 70×70 px y mantiene los enlaces y permisos nativos de Odoo.

Para instalar en otro entorno, copiar el addon a `addons_path`, actualizar la lista de Apps e instalar **DOLAN Theme**. No requiere módulos Enterprise.

## Verificación funcional

El smoke test de Playwright cubre el toggle persistente, la navegación Inicio→grilla→app, iconos de 70 px, modo oscuro legible y viewport móvil:

```bash
cd DOLAN_theme/qa
ODOO_URL=http://localhost:8070 ODOO_DB=dolan \
  ODOO_LOGIN=<usuario> ODOO_PASSWORD=<clave> node theme_v2_e2e.mjs
```

Las credenciales se reciben por variables de entorno y no se guardan en el repositorio. Capturas locales: `docs/evidence/theme-v2-local/`.

## Licencia propuesta

LGPL-3 (compatible con CE y con futura propuesta OCA). Revisar lineamientos OCA antes de publicar.
