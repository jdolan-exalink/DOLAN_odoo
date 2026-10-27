# DOLAN_odoo — Monorepo Odoo 20 CE (Dolan)

Repositorio único (monorepo) para el stack Odoo 20 CE de Dolan y todos los
módulos propios `DOLAN_*`. Repo: <https://github.com/jdolan-exalink/DOLAN_odoo.git>

## Estructura

| Ruta | Qué es |
|---|---|
| `DOLAN_theme/` | Módulo de tema Enterprise Modern (add-on `DOLAN_theme`) + docs/evidencias/qa |
| `DOLAN_ai/` | Módulo `DOLAN_ai`: ChatGPT vía OAuth device flow (más proveedores después) |
| `dolan_dash/`, `dolan_ui/` | Fuentes de los add-ons `dolan_dash` (tablero KPI) y `dolan_ui` (tema/densidad/orden) |
| `DOLAN_XX/` | Convención para los próximos módulos (contabilidad, compras, inventario, …) |
| `odoo20-argentina/` | Stack Docker (compose, Dockerfile, conf, `migration/`, backup) — `addons/` y datos son de runtime y están en `.gitignore` |
| `odd/` | Specs y logs de desarrollo (ODD) por feature |
| `crear_odoo20.sh` | Instalador del stack |

**Modelo de deploy**: la fuente vive en la raíz del monorepo y se copia a
`odoo20-argentina/addons/<modulo>/` para instalar/actualizar en la base `dolan`
(los addons `dolan_dash`/`dolan_ui` hoy tienen la fuente duplicada en
`addons/` — sincronizar al editar).

---

# Odoo 20 CE — Dolan Argentina ERP

Bootstrap repository for the Odoo replacement of the current Dolibarr Argentina multi-company stack.

The product target is **Odoo 20 CE**. Because the official Docker Hub tag `odoo:20.0` may lag behind the upstream source branch, this repository builds a local `dolan-odoo:20.0` image from `odoo/odoo` branch `20.0` by default.

## Quick start

1. Create local environment file:

   ```bash
   cp env.example .env
   ```

2. Review credentials and image/build settings in `.env`.

3. Build the local Odoo 20 image when needed:

   ```bash
   docker compose build odoo
   ```

4. Start and initialize Odoo database `dolan`:

   ```bash
   ./scripts/init_odoo.sh
   ```

5. Check runtime health:

   ```bash
   ./scripts/healthcheck.sh
   ```

Odoo defaults to `http://localhost:8069`.

Local note: if an older Odoo 19 database named `dolan` already exists, do not point Odoo 20 at it directly. This workspace uses `ODOO_DB_NAME=dolan20` in `.env` to keep the old database intact while the Odoo 20 stack is validated.

## Argentina localization strategy

We are building our own addons under `addons/` for the Dolan Argentina stack. Public localization repositories are references for behavior and coverage, not direct runtime dependencies unless a module is explicitly ported and tested for Odoo 20.

Current reference status:

- `ingadhoc/odoo-argentina-ce`: observed branches through `19.0`, no `20.0` branch during this exploration.
- `codize-app/odoo-argentina`: observed branches through `19.0`, no `20.0` branch during this exploration.
- `odoo/odoo`: upstream `20.0` branch exists and is the source for the local image.

Do **not** install Odoo 19 localization addons directly into Odoo 20. Use them to compare accounting/fiscal behavior, then port deliberately into our own modules with tests.

Initial local addon:

- `l10n_ar_dolan_base`: shared fiscal foundation for company fiscal profiles, CUIT, ARCA environment, point-of-sale references, and certificate path references. It does not call ARCA yet.

Architecture note:

- `docs/localizacion-argentina-odoo20.md` records the comparison between AdHoc and Codize references and the proposed Dolan addon split for Argentina accounting/localization.

## Structure

| Path | Purpose |
| --- | --- |
| `docker-compose.yml` | Odoo 20 CE + PostgreSQL stack. Uses `odoo20_data` for the Odoo 20 filestore. |
| `docker/odoo20/Dockerfile` | Local Odoo 20 image built from the official upstream source branch. |
| `config/odoo.conf` | Local bootstrap Odoo config. Keep deployment secrets out of Git. |
| `addons/` | Custom Odoo addons for Argentina localization and migration work. |
| `scripts/init_odoo.sh` | Creates/initializes `dolan` and installs base modules. |
| `scripts/healthcheck.sh` | Verifies Compose services, DB existence, and Odoo HTTP. |
| `scripts/backup.sh` | PostgreSQL + filestore backup helper. |
| `scripts/restore.sh` | Interactive restore helper. |
| `backups/` | Local backup output. |
| `secrets/` | Runtime-only secret mount point. Do not commit real secrets. |

## Current milestone

Hito 1 created the infrastructure. The current work moves the runtime target to Odoo 20 and starts the Argentina localization foundation. ARCA calls, padrón, currency synchronization, POS fiscalization, full accounting reports, and Dolibarr data migration remain later roadmap phases.
