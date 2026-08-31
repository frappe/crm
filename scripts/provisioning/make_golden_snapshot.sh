#!/usr/bin/env bash
# Crea lo "snapshot" (backup del golden site) usato per il provisioning dei
# nuovi clienti. Il golden site è un sito Frappe configurato a mano una volta
# sola: pipeline, status, template email, automazioni, calendari di booking.
#
# Uso (dalla root del bench):
#   ./apps/crm/scripts/provisioning/make_golden_snapshot.sh <golden-site> [output-dir]
#
# Esempio:
#   ./apps/crm/scripts/provisioning/make_golden_snapshot.sh golden.internal ./snapshots
set -euo pipefail

GOLDEN_SITE="${1:?Uso: make_golden_snapshot.sh <golden-site> [output-dir]}"
OUTPUT_DIR="${2:-./snapshots}"

mkdir -p "$OUTPUT_DIR"

echo ">> Backup del golden site '$GOLDEN_SITE' (database + file privati/pubblici)..."
bench --site "$GOLDEN_SITE" backup --with-files

BACKUP_DIR="sites/$GOLDEN_SITE/private/backups"
LATEST_DB=$(ls -t "$BACKUP_DIR"/*-database.sql.gz | head -1)
STAMP=$(date +%Y%m%d-%H%M%S)

cp "$LATEST_DB" "$OUTPUT_DIR/golden-$STAMP-database.sql.gz"
ln -sf "golden-$STAMP-database.sql.gz" "$OUTPUT_DIR/golden-latest.sql.gz"

# file archives (facoltativi: presenti solo se il golden site ha allegati)
for kind in files private-files; do
  latest=$(ls -t "$BACKUP_DIR"/*-$kind.tar 2>/dev/null | head -1 || true)
  if [ -n "$latest" ]; then
    cp "$latest" "$OUTPUT_DIR/golden-$STAMP-$kind.tar"
    ln -sf "golden-$STAMP-$kind.tar" "$OUTPUT_DIR/golden-latest-$kind.tar"
  fi
done

echo ">> Snapshot pronto:"
ls -la "$OUTPUT_DIR" | grep golden-latest
