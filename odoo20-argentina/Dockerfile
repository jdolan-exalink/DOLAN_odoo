FROM odoo:20.0

USER root

RUN apt-get update && apt-get install -y --no-install-recommends     git     build-essential     libssl-dev     swig     python3-dev     libxml2-dev     libxslt1-dev     zlib1g-dev     libsasl2-dev     libldap2-dev     libjpeg-dev     libtiff-dev     libopenjp2-7-dev     libwebp-dev     && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages     git+https://github.com/reingart/pyafipws.git     m2crypto     python-barcode     pdf417gen     qrcode     Pillow     dbf     future

RUN python3 - <<'PY2'
import glob, os
paths = glob.glob('/usr/local/lib/python*/dist-packages/pyafipws/cache')
for p in paths:
    os.makedirs(p, exist_ok=True)
    os.chmod(p, 0o777)
print('pyafipws cache paths:', paths)
PY2

USER odoo
