#!/bin/bash

# Provision a bench for backend-only CI: framework + dependency apps, no
# frontend assets, external MariaDB. Cache hits restore the DB snapshot and
# fast-forward drifted checkouts instead of reinstalling everything.

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
  pilot -b "$BENCH_NAME" set-bench-config mariadb_port "$DB_PORT"
  pilot -b "$BENCH_NAME" set-bench-config mariadb_admin_user root
  pilot -b "$BENCH_NAME" set-bench-config mariadb_password "$DB_ROOT_PASSWORD"
fi
pilot -b "$BENCH_NAME" init --skip-frontend

cd "$BENCH_PATH"

APPS="frappe whatsapp"
pip_apps=(-e "apps/frappe[test]" -e apps/whatsapp)
pilot get-app https://github.com/frappe/whatsapp --skip-assets
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
  APPS="$APPS erpnext"
  pip_apps+=(-e apps/erpnext)
  pilot get-app "https://github.com/frappe/erpnext" --branch "$FRAPPE_BRANCH" --skip-assets
fi

pilot -b "$BENCH_NAME" start > "$RUNNER_TEMP/pilot.log" 2>&1 &
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 1 \
  http://127.0.0.1:7000/api/v1/health

# The external MariaDB service has no utf8mb4 defaults; Frappe needs them.
printf '[client]\nskip-ssl\n' > ~/.my.cnf
mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

# Files whose change means more than new code, requiring reinstall + migrate.
SCHEMA_PATHS=( '*.json' 'hooks.py' 'patches.txt' '*requirements*.txt' 'pyproject.toml' 'setup.py' 'setup.cfg' )
schema_drift=""
refresh_app() {
  local current remote_sha
  current=$(git -C "apps/$1" rev-parse HEAD)
  remote_sha=$(git ls-remote "$(git -C "apps/$1" remote get-url origin)" "$2" | cut -f1)
  [ "$current" != "$remote_sha" ] || return 0
  git -C "apps/$1" fetch --depth 1 origin "$2"
  git -C "apps/$1" diff --quiet HEAD FETCH_HEAD -- "${SCHEMA_PATHS[@]}" || schema_drift=1
  git -C "apps/$1" reset --quiet --hard FETCH_HEAD
}

if [ "$PILOT_CACHE_HIT" != "true" ]; then
  # shellcheck disable=SC2086
  pilot new-site test_site --admin-password admin --apps $APPS --skip-assets
  # Emails resolve CSS through assets.json; tests never load the built bundles.
  mkdir -p sites/assets && echo '{}' > sites/assets/assets.json
  mkdir -p "$HOME/db-snapshot"
  db_name=$(python3 -c "import json; print(json.load(open('sites/test_site/site_config.json'))['db_name'])")
  cp sites/test_site/site_config.json "$HOME/db-snapshot/site_config.json"
  mariadb-dump --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" \
    --single-transaction --quick "$db_name" | gzip > "$HOME/db-snapshot/test_site.sql.gz"
else
  db_name=$(python3 -c "import json; print(json.load(open('sites/test_site/site_config.json'))['db_name'])")
  db_user=$(python3 -c "import json; c = json.load(open('sites/test_site/site_config.json')); print(c.get('db_user') or c['db_name'])")
  db_password=$(python3 -c "import json; print(json.load(open('sites/test_site/site_config.json'))['db_password'])")
  mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS \`$db_name\`"
  mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "CREATE USER IF NOT EXISTS '${db_user}'@'%' IDENTIFIED BY '${db_password}'"
  mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" -e "GRANT ALL PRIVILEGES ON \`$db_name\`.* TO '${db_user}'@'%'"
  gunzip -c "$HOME/db-snapshot/test_site.sql.gz" | mariadb --host "$DB_HOST" --port "$DB_PORT" -u root -p"$DB_ROOT_PASSWORD" "$db_name"
  # Fast-forward cached checkouts; the final migrate below covers schema drift.
  refresh_app frappe "refs/heads/$FRAPPE_BRANCH"
  refresh_app whatsapp HEAD
  if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    refresh_app erpnext "refs/heads/$FRAPPE_BRANCH"
  fi
fi
uv pip install --python env/bin/python "${pip_apps[@]}"
if [ -n "$schema_drift" ]; then
  pilot frappe --site test_site migrate
fi
