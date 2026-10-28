#!/bin/bash
set -euo pipefail
# Backup diario de la DB `dolan` + configs del stack odoo20-argentina.
# Patron del backup de dolibarr (backups/daily + monthly, .sql.gz).
# Cron sugerido (NO se instala automaticamente):
#   0 2 * * * cd /root/DOLAN_odoo20/odoo20-argentina && ./backup-dolan.sh >> backups/backup.log 2>&1

BASE="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE"
STAMP="$(date +%Y%m%d_%H%M%S)"
DAY="$(date +%Y%m%d)"
mkdir -p backups/daily backups/monthly

echo "[$(date -Is)] dump dolan..."
docker compose exec -T db pg_dump -U odoo --dbname=dolan --clean --if-exists \
  | gzip > "backups/daily/dolan_${STAMP}.sql.gz"
gzip -t "backups/daily/dolan_${STAMP}.sql.gz"

echo "[$(date -Is)] configs..."
tar czf "backups/daily/configs_${STAMP}.tar.gz" \
  odoo.conf docker-compose.yml migration/data 2>/dev/null || \
tar czf "backups/daily/configs_${STAMP}.tar.gz" odoo.conf docker-compose.yml

# retencion: 30 dias, 12 mensuales
find backups/daily -name 'dolan_*.sql.gz' -mtime +30 -delete 2>/dev/null || true
find backups/daily -name 'configs_*.tar.gz' -mtime +30 -delete 2>/dev/null || true
if [[ "$(date +%d)" == "01" ]]; then
  cp "backups/daily/dolan_${STAMP}.sql.gz" "backups/monthly/dolan_${STAMP}.sql.gz"
  ls -1t backups/monthly/dolan_*.sql.gz | tail -n +13 | xargs -r rm -f
fi

SIZE="$(du -h "backups/daily/dolan_${STAMP}.sql.gz" | cut -f1)"
echo "[$(date -Is)] OK: backups/daily/dolan_${STAMP}.sql.gz (${SIZE})"
