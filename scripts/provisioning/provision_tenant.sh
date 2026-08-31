#!/usr/bin/env bash
# Crea il sito di un nuovo cliente partendo dallo snapshot del golden site.
#
# Prerequisiti (una tantum sul bench):
#   bench config dns_multitenant on
#   DNS wildcard *.tuobrand.com puntato al server + certificato wildcard
#
# Uso (dalla root del bench):
#   ADMIN_PASSWORD=... MYSQL_ROOT_PASSWORD=... \
#     ./apps/crm/scripts/provisioning/provision_tenant.sh <site-name> [snapshot.sql.gz] [dominio-custom]
#
# Esempi:
#   provision_tenant.sh cliente1.tuobrand.com
#   provision_tenant.sh cliente2.tuobrand.com ./snapshots/golden-latest.sql.gz www.cliente2.it
set -euo pipefail

SITE="${1:?Uso: provision_tenant.sh <site-name> [snapshot.sql.gz] [dominio-custom]}"
SNAPSHOT="${2:-./snapshots/golden-latest.sql.gz}"
CUSTOM_DOMAIN="${3:-}"

ADMIN_PASSWORD="${ADMIN_PASSWORD:?Esporta ADMIN_PASSWORD per Administrator del nuovo sito}"
MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD:?Esporta MYSQL_ROOT_PASSWORD (root del database)}"

if bench --site "$SITE" list-apps >/dev/null 2>&1; then
  echo "!! Il sito $SITE esiste già. Interrompo." >&2
  exit 1
fi

echo ">> Creo il sito $SITE..."
bench new-site "$SITE" \
  --admin-password "$ADMIN_PASSWORD" \
  --db-root-password "$MYSQL_ROOT_PASSWORD" \
  --install-app crm

if [ -f "$SNAPSHOT" ]; then
  echo ">> Restore dello snapshot golden: $SNAPSHOT"
  RESTORE_ARGS=("$SNAPSHOT" --db-root-password "$MYSQL_ROOT_PASSWORD")
  base="${SNAPSHOT%.sql.gz}"
  [ -f "$base-files.tar" ] && RESTORE_ARGS+=(--with-public-files "$base-files.tar")
  [ -f "$base-private-files.tar" ] && RESTORE_ARGS+=(--with-private-files "$base-private-files.tar")
  bench --site "$SITE" restore "${RESTORE_ARGS[@]}"
  # dopo il restore la password admin è quella del golden site: la reimposto
  bench --site "$SITE" set-admin-password "$ADMIN_PASSWORD"
else
  echo ">> Nessuno snapshot trovato ($SNAPSHOT): sito creato vuoto."
fi

echo ">> Migrazioni e build..."
bench --site "$SITE" migrate

if [ -n "$CUSTOM_DOMAIN" ]; then
  echo ">> Aggiungo il dominio custom $CUSTOM_DOMAIN..."
  bench setup add-domain --site "$SITE" "$CUSTOM_DOMAIN"
  echo "   Ricorda: bench setup nginx && riavvio nginx + certificato per $CUSTOM_DOMAIN"
fi

echo ">> Abilito lo scheduler..."
bench --site "$SITE" enable-scheduler

echo ""
echo "== Sito pronto: https://$SITE =="
echo "   Login: Administrator / \$ADMIN_PASSWORD"
echo "   Da fare a mano per questo cliente:"
echo "   - CRM Twilio Settings (credenziali + numeri del cliente)"
echo "   - Email Account (SMTP/IMAP del cliente) + SPF/DKIM/DMARC"
echo "   - WhatsApp Settings se usato"
echo "   - Logo/branding del cliente"
