# Odoo 20 installer + enterprise parity (barcode & l10n_ar)

Baseline installer for Odoo 20 CE with Argentina localization, based on the
existing `crear_odoo.sh` (18/19), plus functional-parity coverage for two
Enterprise areas: barcode operations and AR accounting. Enterprise code is
proprietary (OPL-1): we replicate functionality with community sources, never
copy code.

## Specs

S1: "quiero que arranquemos a desarrollar un script de instalacion basandonos en @crear_odoo.sh pero para odoo 20"
- New script `crear_odoo20.sh` derived from `crear_odoo.sh`, targeting Odoo 20 CE
  (docker image `odoo:20.0`).
- Keep the original interaction model (interactive prompts, optional immediate
  deploy) and extend with non-interactive flags for automation.
- The 19.0 compatibility hack (cloning 18.0 branch) must be removed: use native
  20.0 sources.
- Argentina localization sources for 20.0: `ingadhoc/odoo-argentina-ce` (fiscal
  webservices), `ingadhoc/odoo-argentina` (tax/withholding, bank, purchase,
  ux), `ingadhoc/argentina-sale` (sale/stock AR). Python deps as in the base
  script (pyafipws, python-barcode, etc.).
- Idempotent and safe: validates docker presence, does not clobber an existing
  project directory, aborts cleanly with nonzero exit on failure.

S2: "contabilidad para argentina" (community parity)
- Install must leave the DB ready to install `l10n_ar` (core CE) plus the
  ingadhoc AR localization set for 20.0.
- AFIP/ARCA webservice dependencies (pyafipws, M2Crypto) must build inside the
  image; keep the cache-permissions workaround if still required on 20.0.

S3: "modulos enterprise ... de codigo de barra" (community parity)
- Wire the best available community coverage for barcode operations on 20.0:
  core `barcodes`, product barcode fields, and any migrated OCA module
  (OCA 20.0 barcode repos are mostly unmigrated as of 2026-10; document what
  is and is not covered instead of inventing sources).

S4: "podemos armar una tabla de diferencias entre la CE y ETN"
- `docs/ce-vs-enterprise.md`: side-by-side comparison table CE vs Odoo
  Enterprise for barcode and Argentina accounting (module-by-module: CE core,
  Enterprise module, community replacement, gap/notes). Extensible to other
  areas. Informational only: no copying of Enterprise code, no decompilation.

## Tasks

- T1 [S1,S2] Implement `crear_odoo20.sh` (docker 20.0, deps, AR sources, flags,
  guards). Route: inline. Commit: n/a (repo not under git).
- T2 [S3] Barcode parity wiring: verify available 20.0 community modules and
  include them; document gaps. Route: inline.
- T3 [S4] Write `docs/ce-vs-enterprise.md` difference tables. Route: inline.
- T4 [S1,S2,S3] Verify: bash -n, shellcheck (if available), non-interactive
  dry-run of repo URL checks, help text. Route: inline.

## Log

- L1 (user, verbatim): "ahora que estamos quiero que arranquemos a desarrollar
  un script de instalacion basandonos en @crear_odoo.sh pero para odoo 20 y
  quiero que repliquemos los modulos enterprise de odoo de codigo de barra,
  contabilidad para argentina, podemos armar una tabla de diferencias entre la
  CE y ETN"
- L2 (assistant decision, accepted via "dale" momentum + continuation):
  Enterprise OPL-1 code is never copied or reverse-engineered; parity is via
  community/OCA sources and the difference table documents real gaps.
- L3 (verification evidence, T1-T4): bash -n OK; --help OK; --check OK (3 repos
  20.0 accesibles); smoke test no-interactivo en mktemp genero Dockerfile,
  docker-compose.yml, odoo.conf (postgres:17, password, 20.0), addons README y
  clono los 3 repos con modulos l10n_ar_*; guard de directorio existente OK.
  shellcheck no disponible en el host. Docker build completo no ejecutado
  (requiere pull de imagen ~1GB).
- L4 (deploy real, 2026-10-26): build+up OK sobre odoo20-argentina:8070
  (postgres:17). Bugs encontrados y corregidos en crear_odoo20.sh: (1) flag
  --deploy no disparaba compose (regex de confirmacion); (2) Odoo 20 hace bind
  en 127.0.0.1 por defecto -> agregado http_interface=0.0.0.0 a odoo.conf; (3)
  glob de cache pyafipws no matcheaba (dist-packages/pyafipws/cache inexistente)
  -> corregido a crear el dir bajo pyafipws/. Agregados 3 repos ingadhoc con
  dependencias transversales: account-financial-tools, account-payment, sale
  (account_internal_transfer, account_payment_pro, sale_ux). Instalacion
  headless verificada sobre base argentina_test: 56 modulos, 20 instalados
  entre los nuestros (l10n_ar, l10n_ar_purchase, l10n_ar_ux,
  account_internal_transfer + 16 ux/compat), 50 cuentas AR creadas, UI HTTP 200.
- L5 (hallazgo de alcance, decision pendiente): los modulos AR clave de
  ingadhoc para 20.0 (l10n_ar_fiscal_ws = facturacion electronica, l10n_ar_tax,
  l10n_ar_bank, l10n_ar_sale, sale_ux, account_payment_pro) tienen
  installable: False en branch 20.0 (migracion WIP, Odoo 20 liberado ~2026-10-15).
  Opciones documentadas en docs/ce-vs-enterprise.md 2.1: esperar ingadhoc,
  base Odoo 19, o port propio del fiscal_ws 19.0->20.0. Usuario decidira.
