#!/bin/bash

# Provision-only: installs pilot, creates the bench, builds the framework and
# dependency apps, and creates the dependency-only site. The site database is
# dumped to ~/db-snapshot on a cache miss; the app under test is installed
# per-run afterwards, so cached runs always test fresh PR code.
#
# Expects from the caller: FRAPPE_BRANCH, INSTALL_ERPNEXT, PILOT_CACHE_HIT
# ("true" when the bench was restored, anything else provisions from scratch).

set -eo pipefail

FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
BENCH_NAME="frappe-bench"
BENCH_PATH="$HOME/pilot/benches/$BENCH_NAME"
PILOT_CACHE_HIT="${PILOT_CACHE_HIT:-}"
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_ROOT_PASSWORD="root"

export PATH="$HOME/pilot/bin:$HOME/.local/bin:$PATH"
printf '%s\n' "$HOME/pilot/bin" "$HOME/.local/bin" >> "$GITHUB_PATH"

curl -fsSL "https://raw.githubusercontent.com/frappe/pilot/develop/install.sh" | sh -s -- --ci

if [ ! -d "$BENCH_PATH" ]; then
  pilot new "$BENCH_NAME" --frappe-branch "$FRAPPE_BRANCH"
  pilot -b "$BENCH_NAME" set-bench-config admin_allow_site_to_pilot_communication false
  pilot -b "$BENCH_NAME" set-bench-config mariadb_existing true
  pilot -b "$BENCH_NAME" set-bench-config mariadb_host "$DB_HOST"
  pilot -b "$BENCH_NAME" set-bench-config mariadb_port 3306
  pilot -b "$BENCH_NAME" set-bench-config mariadb_admin_user root
  pilot -b "$BENCH_NAME" set-bench-config mariadb_password "$DB_ROOT_PASSWORD"
fi
pilot -b "$BENCH_NAME" init --skip-frontend

cd "$BENCH_PATH"

# uv is used by pilot/suite CI for the test extras
uv pip install --python env/bin/python -e "apps/frappe[test]"

pilot get-app https://github.com/frappe/whatsapp --skip-assets
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
  pilot get-app https://github.com/frappe/erpnext --branch "$FRAPPE_BRANCH" --skip-assets
fi

# Start pilot services in background (caller waits on health)
pilot -b "$BENCH_NAME" start > "$RUNNER_TEMP/pilot.log" 2>&1 &
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 1 \
  http://127.0.0.1:7000/api/v1/health

if [ "$PILOT_CACHE_HIT" != "true" ]; then
  # The external MariaDB service has no utf8mb4 defaults; Frappe needs them.
  printf '[client]\nskip-ssl\n' > ~/.my.cnf
  mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "SET GLOBAL character_set_server = 'utf8mb4'"
  mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

  APPS="frappe whatsapp"
  if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    APPS="frappe whatsapp erpnext"
  fi
  # shellcheck disable=SC2086
  pilot new-site test_site --admin-password admin --apps $APPS --skip-assets
  # Emails resolve CSS through assets.json; tests never load the built bundles.
  mkdir -p sites/assets && echo '{}' > sites/assets/assets.json

  mkdir -p "$HOME/db-snapshot"
  db_name=$(python3 -c "import json; print(json.load(open('sites/test_site/site_config.json'))['db_name'])")
  cp sites/test_site/site_config.json "$HOME/db-snapshot/site_config.json"
  mariadb-dump --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" \
    --single-transaction --quick "$db_name" | gzip > "$HOME/db-snapshot/test_site.sql.gz"
fi
