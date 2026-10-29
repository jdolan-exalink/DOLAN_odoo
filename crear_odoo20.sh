#!/bin/bash
set -euo pipefail
# Directorio propio del script (absoluto, antes de cualquier cd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Deploy Odoo 20 CE + Localizacion Argentina (comunidad)
# Basado en crear_odoo.sh (18/19). Odoo 20 usa fuentes nativas 20.0:
#   - ingadhoc/odoo-argentina-ce   -> webservices AFIP/ARCA (WSFEv1, WSAA)
#   - ingadhoc/odoo-argentina      -> retenciones/percepciones, bancos, compras
#   - ingadhoc/argentina-sale      -> ventas/stock con regimen AR
# Enterprise es propietario (OPL-1): la paridad se arma con fuentes community.
# ---------------------------------------------------------------------------

ODOO_VERSION="20.0"
AR_REPOS=(
  "https://github.com/ingadhoc/odoo-argentina-ce.git"
  "https://github.com/ingadhoc/odoo-argentina.git"
  "https://github.com/ingadhoc/argentina-sale.git"
  "https://github.com/ingadhoc/account-financial-tools.git"
  "https://github.com/ingadhoc/account-payment.git"
  "https://github.com/ingadhoc/sale.git"
)

usage() {
  cat <<'USAGE'
Uso: crear_odoo20.sh [opciones]

  -n, --name NOMBRE       Nombre del proyecto (default: odoo20-argentina)
  -p, --port PUERTO       Puerto para acceder a Odoo (default: 8070)
  -a, --admin-pass PASS   Contrasena admin para odoo.conf (default: aleatoria)
      --deploy            Desplegar con docker compose al terminar
      --no-deploy         No desplegar (solo generar el proyecto)
      --init-db NOMBRE    Crear/inicializar la DB NOMBRE tras el deploy: instala
                          el bundle de apps de negocio (estilo enterprise) y
                          oculta los tiles Enterprise (OEEL-1) del menu Apps
      --apps "A,B,C"      Lista de apps a instalar en --init-db
                          (default: sale_management,point_of_sale,mrp,project,crm,hr_expense)
      --check             Solo validar conectividad a los repos y salir
      --non-interactive   No preguntar nada; exige -n/-p/-a o usa defaults
  -h, --help              Mostrar esta ayuda

Sin opciones el script pregunta igual que la version anterior.
USAGE
}

PROJECT_NAME=""
PORT=""
ADMIN_PASSWD=""
DEPLOY=""
INTERACTIVE=1
CHECK_ONLY=0
INIT_DB=""
# Bundle "estilo enterprise": apps CE de negocio que ETN trae de serie.
# Los 19 modulos OEEL-1 (enterprise) se ocultan del menu Apps en la init.
SYSTEM_APPS="sale_management,point_of_sale,mrp,project,crm,hr_expense"
# Addons propios del stack: dolan_dash (dashboard) y dolan_ui (orden de apps
# y app por defecto). Se copian desde el deploy canonico (odoo20-argentina/addons).
# NOTA: web_responsive (OCA 19.0) NO se instala: su JS es Owl2 y Odoo 20 usa
# Owl3 (crash de AppsMenu -> pantalla blanca). Esperar migracion oficial 20.0.
CUSTOM_ADDONS="DOLAN_theme DOLAN_ai DOLAN_alquileres DOLAN_bancos DOLAN_calidad DOLAN_codigo_barras DOLAN_contabilidad DOLAN_declaracion DOLAN_flotilla DOLAN_mantenimiento DOLAN_suscripciones DOLAN_taller dolan_dash dolan_ui"

# Paridad de Contabilidad (S8): módulos que se instalan además de los custom.
# l10n_latam_check es core; los demás vienen de OCA rama 19.0 con port 19->20
# aplicado más abajo (docs/ee-parity-contabilidad.md §7). OCA todavía no tiene
# ramas 20.0 utilizables (scaffolding vacío).
#   report_xlsx / report_xlsx_helper : dependencias de reportes
#   date_range                       : dependencia de account_financial_report
#   partner_statement                : estados de cuenta del contacto (C6)
# NO incluidos (port pendiente, ver §7): account_financial_report (Odoo 20
# eliminó el modelo account.group) y auditlog (modelo SQL-view sin tabla).
PARITY_ADDONS="l10n_latam_check report_xlsx report_xlsx_helper date_range partner_statement"
OCA_REPOS=(
  "https://github.com/OCA/reporting-engine.git"
  "https://github.com/OCA/account-financial-reporting.git"
  "https://github.com/OCA/server-ux.git"
)
OCA_BRANCH="19.0"
OCA_MODULES_WANTED="report_xlsx report_xlsx_helper date_range partner_statement"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -n|--name) PROJECT_NAME="$2"; shift 2 ;;
    -p|--port) PORT="$2"; shift 2 ;;
    -a|--admin-pass) ADMIN_PASSWD="$2"; shift 2 ;;
    --deploy) DEPLOY="S"; shift ;;
    --no-deploy) DEPLOY="n"; shift ;;
    --init-db) INIT_DB="$2"; shift 2 ;;
    --apps) SYSTEM_APPS="$2"; shift 2 ;;
    --check) CHECK_ONLY=1; shift ;;
    --non-interactive) INTERACTIVE=0; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Opcion desconocida: $1" >&2; usage >&2; exit 1 ;;
  esac
done

echo "----------------------------------"
echo "Deploy Odoo CE 20 + Localizacion Argentina"
echo "----------------------------------"

if [[ $CHECK_ONLY -eq 1 ]]; then
  rc=0
  for repo in "${AR_REPOS[@]}"; do
    branch="20.0"
    if git ls-remote --heads "$repo" "$branch" | grep -q "$branch"; then
      echo "OK: $repo ($branch accesible)"
    else
      echo "FALLO: $repo (branch $branch inaccesible)" >&2
      rc=1
    fi
  done
  exit $rc
fi

if [[ $INTERACTIVE -eq 1 ]]; then
  if [[ -z "$PROJECT_NAME" ]]; then
    read -p "Nombre del proyecto (ej: odoo-argentina20): " PROJECT_NAME
  fi
  if [[ -z "$PORT" ]]; then
    read -p "Puerto para acceder a Odoo (ej: 8070): " PORT
  fi
  if [[ -z "$ADMIN_PASSWD" ]]; then
    read -p "Contrasena ADMIN para odoo.conf: " ADMIN_PASSWD
  fi
fi

PROJECT_NAME=${PROJECT_NAME:-odoo20-argentina}
PORT=${PORT:-8070}
ADMIN_PASSWD=${ADMIN_PASSWD:-$(head -c 18 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9')}

if [[ -e "$PROJECT_NAME" ]]; then
  echo "Error: '$PROJECT_NAME' ya existe. Elegi otro nombre." >&2
  exit 1
fi

if [[ "$DEPLOY" == "yes" || ($INTERACTIVE -eq 1 && -z "$DEPLOY") ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker no esta instalado (necesario para desplegar)." >&2
    exit 1
  fi
  if ! docker compose version >/dev/null 2>&1; then
    echo "Error: docker compose (plugin) no esta disponible." >&2
    exit 1
  fi
fi

mkdir -p "$PROJECT_NAME"/{addons,odoo-data,db-data}
chown -R 101:101 "$PROJECT_NAME/odoo-data" "$PROJECT_NAME/addons" "$PROJECT_NAME/db-data"
chmod -R 775 "$PROJECT_NAME/odoo-data" "$PROJECT_NAME/addons" "$PROJECT_NAME/db-data"

cd "$PROJECT_NAME"

cat > Dockerfile <<EOF
FROM odoo:${ODOO_VERSION}

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    libssl-dev \
    swig \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libsasl2-dev \
    libldap2-dev \
    libjpeg-dev \
    libtiff-dev \
    libopenjp2-7-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages \
    git+https://github.com/reingart/pyafipws.git \
    m2crypto \
    python-barcode \
    pdf417gen \
    qrcode \
    Pillow \
    dbf \
    future \
    pypdfium2

RUN python3 - <<'PY2'
import glob, os
packages = glob.glob('/usr/local/lib/python*/dist-packages/pyafipws') + \
           glob.glob('/usr/local/lib/python*/site-packages/pyafipws')
for p in packages:
    cache = os.path.join(p, 'cache')
    os.makedirs(cache, exist_ok=True)
    os.chmod(cache, 0o777)
print('pyafipws cache dirs:', packages)
PY2

USER odoo
EOF

cat > docker-compose.yml <<EOF
services:
  db:
    image: postgres:17
    container_name: ${PROJECT_NAME}_db
    environment:
      POSTGRES_DB: postgres
      POSTGRES_USER: odoo
      POSTGRES_PASSWORD: odoo
    volumes:
      - ./db-data:/var/lib/postgresql/data
    restart: always

  odoo:
    build: .
    container_name: ${PROJECT_NAME}_odoo
    depends_on:
      - db
    ports:
      - "${PORT}:8069"
    volumes:
      - ./addons:/mnt/extra-addons
      - ./odoo-data:/var/lib/odoo
      - ./odoo.conf:/etc/odoo/odoo.conf
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=odoo
    restart: always
EOF

cat > odoo.conf <<EOF
[options]
admin_passwd = ${ADMIN_PASSWD}
db_host = db
db_port = 5432
db_user = odoo
db_password = odoo
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
http_interface = 0.0.0.0
logfile = /var/log/odoo/odoo.log
workers = 0
EOF

echo "Descargando modulos Localizacion Argentina (branch ${ODOO_VERSION})..."
cd addons
for repo in "${AR_REPOS[@]}"; do
  name="$(basename "$repo" .git)"
  echo "  -> $name (branch ${ODOO_VERSION})"
  git clone --depth 1 --branch "${ODOO_VERSION}" "$repo"
  shopt -s dotglob nullglob
  mv "$name"/* . 2>/dev/null || true
  rm -rf "$name"
done

# El port de l10n_ar_fiscal_ws (facturacion electronica AFIP/ARCA) existe en
# la branch 20.0 de ingadhoc pero con installable:False (repo WIP). Nuestro
# stack lo habilita y lo valida (suite de tests en verde, ver
# odd/tasks/port-fiscal-ws-20.md). Otros modulos AR siguen WIP: no se tocan.
if [[ -f l10n_ar_fiscal_ws/__manifest__.py ]]; then
  sed -i 's/"installable": False/"installable": True/' l10n_ar_fiscal_ws/__manifest__.py
  echo "  -> l10n_ar_fiscal_ws habilitado (port validado 2026-10-26)"
fi
cd ..

# ---------------------------------------------------------------------------
# OCA 19.0 + port 19->20 para la paridad de Contabilidad (S8/L47).
# Sólo los módulos de PARITY_ADDONS; se aplanan en addons/ como los de ingadhoc.
# ---------------------------------------------------------------------------
echo "Descargando módulos OCA (branch ${OCA_BRANCH} + port 19->20)..."
cd addons
for repo in "${OCA_REPOS[@]}"; do
  name="$(basename "$repo" .git)"
  echo "  -> $name (branch ${OCA_BRANCH})"
  git clone --depth 1 --branch "${OCA_BRANCH}" "$repo" ".oca_${name}" >/dev/null 2>&1 || {
    echo "     FALLÓ el clone de $name"; continue; }
  for m in $OCA_MODULES_WANTED; do
    if [[ -d ".oca_${name}/$m" ]]; then
      rm -rf "$m"; cp -r ".oca_${name}/$m" "$m"; echo "     + $m"
    fi
  done
  rm -rf ".oca_${name}"
done

python3 - <<'OCA_PORT_19_TO_20'
import csv, pathlib, re

MODS = ["report_xlsx", "report_xlsx_helper", "date_range", "partner_statement"]

def operation(perm):
    out = ""
    if perm.get("perm_create") == "1": out += "c"
    if perm.get("perm_read") == "1": out += "r"
    if perm.get("perm_write") == "1": out += "u"
    if perm.get("perm_unlink") == "1": out += "d"
    return out

for m in MODS:
    root = pathlib.Path(m)
    if not root.exists():
        continue
    # 1) CSV de permisos: ir.model.access.csv -> ir.access.csv, perm_* -> operation
    for c in list(root.rglob("ir.model.access.csv")):
        rows = list(csv.reader(c.open(newline="", encoding="utf-8")))
        out = [["id", "name", "model_id:id", "group_id:id", "operation", "domain"]]
        if rows and "perm_read" in rows[0]:
            idx = {n: i for i, n in enumerate(rows[0])}
            for r in rows[1:]:
                if not r or not any(r):
                    continue
                get = lambda k: (r[idx[k]].strip() if k in idx and idx[k] < len(r) else "")
                out.append([get("id"), get("name"), get("model_id:id"), get("group_id:id"),
                            operation({k: get(k) for k in ("perm_read", "perm_write",
                                                           "perm_create", "perm_unlink")}), ""])
        else:
            out = rows
        c.with_name("ir.access.csv").write_text(
            "\n".join(",".join(row) for row in out) + "\n", encoding="utf-8")
        if c.name != "ir.access.csv":
            c.unlink()  # el CSV viejo ya no lo referencia el manifest
        print(f"     port: {m}/security/ir.model.access.csv -> ir.access.csv (operation)")
    # 2) manifest: nombre del CSV, version 20.0, installable True
    man = root / "__manifest__.py"
    if man.exists():
        txt = man.read_text(encoding="utf-8")
        new = txt.replace("security/ir.model.access.csv", "security/ir.access.csv")
        new = re.sub(r'"version": "19\.0\.', '"version": "20.0.', new)
        new = re.sub(r"(['\"])installable\1\s*:\s*False", '"installable": True', new)
        if new != txt:
            man.write_text(new, encoding="utf-8")
            print(f"     port: {m}/__manifest__.py (version 20.0 / csv / installable)")
    # 3) XML: ir.rule -> ir.access (domain + operation obligatoria) y sin report_file
    for x in root.rglob("*.xml"):
        txt = x.read_text(encoding="utf-8", errors="replace")
        if ('model="ir.rule"' not in txt and 'name="domain_force"' not in txt
                and 'name="report_file"' not in txt):
            continue
        new = txt.replace('model="ir.rule"', 'model="ir.access"')
        new = new.replace('name="domain_force"', 'name="domain"')
        new = re.sub(r'\s*<field name="global"[^/]*/>\n', "\n", new)
        new = re.sub(r'\s*<field name="report_file">[^<]*</field>', "", new)
        def _add_op(match):
            block = match.group(0)
            if 'model="ir.access"' not in block or 'name="operation"' in block:
                return block
            return re.sub(r'(<field name="name">[^<]*</field>\s*)',
                          r'\1<field name="operation">crud</field>\n        ', block, count=1)
        new = re.sub(r'<record[^>]*>.*?</record>', _add_op, new, flags=re.S)
        if new != txt:
            x.write_text(new, encoding="utf-8")
            print(f"     port: {x}")
    # 4) imports movidos en Odoo 20
    for py in root.rglob("*.py"):
        txt = py.read_text(encoding="utf-8", errors="replace")
        new = txt
        if "content_disposition" in new:
            new = new.replace("from odoo.http import content_disposition, request, route",
                              "from odoo.http.stream import content_disposition\n"
                              "from odoo.http import request, route")
            new = new.replace("from odoo.http import content_disposition",
                              "from odoo.http.stream import content_disposition")
            new = re.sub(r"from odoo\.http import \(\s*content_disposition,\s*",
                         "from odoo.http.stream import content_disposition\nfrom odoo.http import (\n    ", new)
        if "serialize_exception" in new:
            new = new.replace("from odoo.http import serialize_exception",
                              "from odoo.http.dispatcher import serialize_exception")
            new = re.sub(r"from odoo\.http import \(\s*serialize_exception as (_serialize_exception),",
                         "from odoo.http.dispatcher import (\n    serialize_exception as \\1,", new)
        if new != txt:
            py.write_text(new, encoding="utf-8")
            print(f"     port: {py} (imports odoo.http -> stream/dispatcher)")
print("port OCA 19->20 aplicado")
OCA_PORT_19_TO_20
cd ..

cat > addons/README.md <<'EOF'
# Addons de Localizacion Argentina (Odoo 20 CE)

Fuentes community (branch 20.0), descargadas por crear_odoo20.sh:

OCA (paridad de Contabilidad, S8): crear_odoo20.sh también clona la branch
19.0 de OCA/reporting-engine, OCA/account-financial-reporting y OCA/server-ux
(sus ramas 20.0 siguen vacías), copia sólo report_xlsx, report_xlsx_helper,
date_range y partner_statement, y les aplica el port 19->20 (CSV
ir.access/operation, ir.rule->ir.access, imports odoo.http, report_file,
version 20.0). NO copia account_financial_report ni auditlog: sus ports
están pendientes (docs/ee-parity-contabilidad.md §7).

- ingadhoc/odoo-argentina-ce: l10n_ar_fiscal_ws* (WSAA / WSFEv1 AFIP-ARCA)
- ingadhoc/odoo-argentina: l10n_ar_tax, l10n_ar_bank, l10n_ar_purchase*, l10n_ar_ux
- ingadhoc/argentina-sale: l10n_ar_sale*, l10n_ar_stock*, preimpresos
- ingadhoc/account-financial-tools, account-payment, sale: dependencias
  transversales (account_internal_transfer, account_payment_pro, sale_ux, ...)

La localizacion contable base (plan de cuentas, impuestos, tipos de
comprobante, monotributo, retenciones core) es el modulo CORE de Odoo CE:
`l10n_ar` + `l10n_ar_withholding`.

ATENCION (2026-10-26): la migracion a 20.0 de ingadhoc esta en curso. Modulos
clave todavia con installable: False: l10n_ar_tax, l10n_ar_bank, l10n_ar_sale,
sale_ux, account_payment_pro. Ver docs/ce-vs-enterprise.md para el estado
verificado.

l10n_ar_fiscal_ws (facturacion electronica AFIP/ARCA) esta HABILITADO por
crear_odoo20.sh: su port 20.0 de ADHOC instala limpio y su suite de tests
pasa en verde (38/38) sobre este stack. En Ajustes hay que cargar el
certificado X.509 y la clave privada, y elegir homologacion o produccion.
Default de entorno: homologacion hasta que se setee el parametro
l10n_ar_fiscal_ws.env_type=production (mas seguro: sin certificados la
facturacion en homologacion es local).

Cobertura de codigo de barras: modulo core `barcodes` +
`barcodes_gs1_nomenclature` + `sale_barcode`/`sale_price_checker` de
ingadhoc/sale (instalables en 20.0). La UI de escaneo completo de Enterprise
(stock_barcode) no tiene equivalente OCA migrado a 20.0 todavia.
EOF

if [[ -z "$DEPLOY" ]]; then
  read -p "Queres desplegar ahora? (S/n): " DEPLOY
fi
if [[ "${DEPLOY:-S}" =~ ^[SsYy] ]]; then
  echo "Construyendo y levantando contenedores..."
  docker compose build
  docker compose up -d
  echo "Odoo desplegado en http://$(hostname -I | awk '{print $1}'):${PORT}"
else
  echo "Deploy manual: cd ${PROJECT_NAME} && docker compose build && docker compose up -d"
fi

echo "----------------------------------"
echo "Proyecto ${PROJECT_NAME} (Odoo ${ODOO_VERSION}) creado"
echo "Certificados AFIP y parametrizacion se completan desde interfaz web"
echo "----------------------------------"

if [[ -n "$INIT_DB" ]]; then
  # addons propios: copiar desde el deploy canonico (o clonar OCA si falta)
  REF_ADDONS="$SCRIPT_DIR/odoo20-argentina/addons"
  for m in $CUSTOM_ADDONS; do
    if [[ -d "$REF_ADDONS/$m" && ! -d "addons/$m" ]]; then
      cp -r "$REF_ADDONS/$m" addons/
      echo "  addon copiado: $m"
    fi
  done
  echo "Inicializando DB '${INIT_DB}' (apps: ${SYSTEM_APPS} + custom: ${CUSTOM_ADDONS})..."
  docker compose exec -T odoo odoo --config=/etc/odoo/odoo.conf --logfile= \
    --stop-after-init --without-demo=all -d "$INIT_DB" -i "$SYSTEM_APPS,${CUSTOM_ADDONS// /,},${PARITY_ADDONS// /,}" 2>&1 \
    | grep -E "ERROR|CRITICAL|Modules loaded|Registry loaded" | tail -5
  # Ocultar los tiles Enterprise (OEEL-1): no instalables en CE y solo ensucian el menu.
  docker compose exec -T db psql -U odoo -d "$INIT_DB" -c \
    "UPDATE ir_module_module SET application=false WHERE license='OEEL-1' AND application=true;"
  # Entorno fiscal seguro por defecto (homologacion hasta configurar certificados)
  docker compose exec -T db psql -U odoo -d "$INIT_DB" -c \
    "INSERT INTO ir_config_parameter (key,value,create_uid,create_date,write_uid,write_date)
     VALUES ('l10n_ar_fiscal_ws.env_type','homologation',1,now(),1,now())
     ON CONFLICT (key) DO NOTHING;" 2>/dev/null || true
  echo "DB '${INIT_DB}' lista: apps de negocio instaladas y tiles enterprise ocultos"

  # --- Post-deploy setup (usuarios, backup, env_type) ---
  echo "Configurando usuarios..."
  docker compose exec -T db psql -U odoo -d "$INIT_DB" -c \
    "UPDATE res_users SET password='Dolan2026!' WHERE login='admin';"
  docker compose exec -T odoo odoo --config=/etc/odoo/odoo.conf --logfile= --stop-after-init \
    -d "$INIT_DB" --load-language=es_AR 2>&1 | tail -1

  # Cambiar login del admin a admin@DOMINIO (el superuser no se borra)
  ADMIN_EMAIL="${ADMIN_EMAIL:-admin@dolan.com.ar}"
  docker compose exec -T db psql -U odoo -d "$INIT_DB" -c \
    "UPDATE res_users SET login='${ADMIN_EMAIL}' WHERE login='admin';"

  # backup-dolan.sh: copiar al proyecto si está disponible
  if [[ -f "$SCRIPT_DIR/odoo20-argentina/backup-dolan.sh" ]]; then
    cp "$SCRIPT_DIR/odoo20-argentina/backup-dolan.sh" .
    chmod +x backup-dolan.sh
    echo "  backup-dolan.sh copiado (configurar cron: 0 2 * * * cd $(pwd) && ./backup-dolan.sh)"
  fi

  # WSAA: production por defecto (los certs de Dolibarr son production)
  docker compose exec -T db psql -U odoo -d "$INIT_DB" -c \
    "UPDATE ir_config_parameter SET value='production' WHERE key='l10n_ar_fiscal_ws.env_type';"

  # Copiar scripts de QA
  if [[ -d "$SCRIPT_DIR/DOLAN_theme/qa" ]]; then
    mkdir -p qa && cp -r "$SCRIPT_DIR/DOLAN_theme/qa"/* qa/ 2>/dev/null
    echo "  qa/ scripts copiados"
  fi

  echo "Post-deploy setup completo. Accedé en http://<ip>:${PORT}"
fi
