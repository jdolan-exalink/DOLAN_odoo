#!/bin/bash
set -euo pipefail

echo "----------------------------------"
echo "Deploy Odoo CE + Localizacion Argentina"
echo "----------------------------------"

read -p "Version Odoo CE (18.0 / 19.0) [19.0]: " ODOO_VERSION
ODOO_VERSION=${ODOO_VERSION:-19.0}
if [[ "$ODOO_VERSION" != "18.0" && "$ODOO_VERSION" != "19.0" ]]; then
  echo "Version invalida: $ODOO_VERSION (usar 18.0 o 19.0)"
  exit 1
fi

read -p "Nombre del proyecto (ej: odoo-argentina19): " PROJECT_NAME
read -p "Puerto para acceder a Odoo (ej: 8070): " PORT
read -p "Contrasena ADMIN para odoo.conf: " ADMIN_PASSWD

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
    libffi-dev \
    libtiff5-dev \
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
    future

RUN python3 - <<'PY2'
import glob, os
paths = glob.glob('/usr/local/lib/python*/dist-packages/pyafipws/cache')
for p in paths:
    os.makedirs(p, exist_ok=True)
    os.chmod(p, 0o777)
print('pyafipws cache paths:', paths)
PY2

USER odoo
EOF

cat > docker-compose.yml <<EOF
services:
  db:
    image: postgres:15
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
logfile = /var/log/odoo/odoo.log
workers = 0
EOF

echo "Descargando modulos Localizacion Argentina (rama ${ODOO_VERSION})..."
cd addons
if [[ "$ODOO_VERSION" == "19.0" ]]; then
  # For v19, clone v18 branch and we'll fix compatibility
  echo "Nota: Odoo 19.0 usa modulos de 18.0 con ajustes de compatibilidad..."
  git clone --depth 1 --branch "18.0" https://github.com/ingadhoc/odoo-argentina-ce.git
else
  git clone --depth 1 --branch "${ODOO_VERSION}" https://github.com/ingadhoc/odoo-argentina-ce.git
fi
shopt -s dotglob nullglob
mv odoo-argentina-ce/* . 2>/dev/null || true
rm -rf odoo-argentina-ce
cd ..

echo "----------------------------------"
echo "Proyecto ${PROJECT_NAME} (Odoo ${ODOO_VERSION}) creado"
echo "----------------------------------"

read -p "Querés desplegar ahora? (S/n): " DEPLOY_NOW
DEPLOY_NOW=${DEPLOY_NOW:-S}
if [[ "$DEPLOY_NOW" =~ ^[Ss]$ ]]; then
  echo "Construyendo y levantando contenedores..."
  docker compose build
  docker compose up -d
  echo "Odoo desplegado en http://$(hostname -I | awk '{print $1}'):${PORT}"
else
  echo "Deploy manual: cd ${PROJECT_NAME} && docker compose build && docker compose up -d"
fi

echo "----------------------------------"
echo "Certificados AFIP y parametrizacion se completan desde interfaz web"
echo "----------------------------------"
