#!/bin/bash

# Provision-only: installs pilot, creates the bench, builds the framework and
# dependency apps, and prepares the dependency-only site. The site database is
# dumped to ~/db-snapshot on a cache miss; the app under test is installed
# per-run afterwards, so cached runs always test fresh PR code.
#
# Cache hits come in two flavors, told apart by PILOT_CACHE_PRIMARY (the key
# for this run's dependencies) vs PILOT_CACHE_MATCHED (the key that was found):
# exact hits restore and go; prefix-fallback hits refresh framework code,
# reinstall requirements and migrate the restored site forward instead of
# paying for a full reprovision.
#
# Expects from the caller: FRAPPE_BRANCH, INSTALL_ERPNEXT, PILOT_CACHE_PRIMARY,
# PILOT_CACHE_MATCHED (empty when nothing was restored).

set -eo pipefail

FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
BENCH_NAME="frappe-bench"
BENCH_PATH="$HOME/pilot/benches/$BENCH_NAME"
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
pip_apps=(-e "apps/frappe[test]" -e apps/whatsapp)
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
  pip_apps+=(-e apps/erpnext)
fi
uv pip install --python env/bin/python "${pip_apps[@]}"

pilot get-app https://github.com/frappe/whatsapp --skip-assets
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
  pilot get-app https://github.com/frappe/erpnext --branch "$FRAPPE_BRANCH" --skip-assets
fi

# Start pilot services in background (caller waits on health)
pilot -b "$BENCH_NAME" start > "$RUNNER_TEMP/pilot.log" 2>&1 &
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 1 \
  http://127.0.0.1:7000/api/v1/health

# The external MariaDB service has no utf8mb4 defaults; Frappe needs them.
printf '[client]\nskip-ssl\n' > ~/.my.cnf
mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

restore_snapshot() {
  db_name=$(python3 -c "import json; print(json.load(open('sites/test_site/site_config.json'))['db_name'])")
  db_user=$(python3 -c "import json; c = json.load(open('sites/test_site/site_config.json')); print(c.get('db_user') or c['db_name'])")
  db_password=$(python3 -c "import json; print(json.load(open('sites/test_site/site_config.json'))['db_password'])")
  mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`$db_name\`"
  mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "CREATE USER IF NOT EXISTS '${db_user}'@'%' IDENTIFIED BY '${db_password}'"
  mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "GRANT ALL PRIVILEGES ON \`$db_name\`.* TO '${db_user}'@'%'"
  gunzip -c "$HOME/db-snapshot/test_site.sql.gz" | mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" "$db_name"
}

if [ -z "$PILOT_CACHE_MATCHED" ]; then
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
elif [ "$PILOT_CACHE_MATCHED" != "$PILOT_CACHE_PRIMARY" ]; then
  restore_snapshot
  # Framework moved under a cached bench: pull the new code, reinstall
  # requirements and migrate the restored site forward instead of rebuilding.
  git -C apps/frappe fetch --depth 1 origin "$FRAPPE_BRANCH"
  git -C apps/frappe reset --hard FETCH_HEAD
  git -C apps/whatsapp fetch --depth 1 origin HEAD
  git -C apps/whatsapp reset --hard FETCH_HEAD
  if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    git -C apps/erpnext fetch --depth 1 origin "$FRAPPE_BRANCH"
    git -C apps/erpnext reset --hard FETCH_HEAD
  fi
  uv pip install --python env/bin/python "${pip_apps[@]}"
  pilot frappe --site test_site migrate
else
  restore_snapshot
fi
