#!/bin/bash

set -eo pipefail

FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
<<<<<<< HEAD
<<<<<<< HEAD
FRAPPE_REF=$(bash "${GITHUB_WORKSPACE}/.github/helper/frappe_ref.sh" "${FRAPPE_BRANCH}")
=======
PILOT_VERSION="v0.0.99-pre-alpha"
=======
>>>>>>> c19df28 (ci: track pilot develop, drop version pin)
BENCH_NAME="frappe-bench"
BENCH_PATH="$HOME/pilot/benches/$BENCH_NAME"
>>>>>>> 1401ab8 (ci: use pilot with skip-frontend/skip-assets for server tests)

export PATH="$HOME/pilot/bin:$HOME/.local/bin:$PATH"

<<<<<<< HEAD
<<<<<<< HEAD
pip install frappe-bench
[ -d ~/frappe ] || git clone "https://github.com/frappe/frappe" --branch "${FRAPPE_REF}" --depth 1
bench init --skip-assets --frappe-path ~/frappe --python "$(which python)" frappe-bench
=======
curl -fsSL "https://raw.githubusercontent.com/frappe/pilot/${PILOT_VERSION}/install.sh" | sh -s -- --version "$PILOT_VERSION"
>>>>>>> 1401ab8 (ci: use pilot with skip-frontend/skip-assets for server tests)
=======
curl -fsSL "https://raw.githubusercontent.com/frappe/pilot/develop/install.sh" | sh
>>>>>>> c19df28 (ci: track pilot develop, drop version pin)

pilot new "$BENCH_NAME" --frappe-branch "$FRAPPE_BRANCH"
pilot -b "$BENCH_NAME" init --skip-frontend

BENCH_DIR="$BENCH_PATH"
cd "$BENCH_DIR"

# uv is used by pilot/suite CI for the test extras
uv pip install --python env/bin/python -e "apps/frappe[test]"

pilot get-app https://github.com/frappe/whatsapp --skip-assets
pilot get-app "$GITHUB_WORKSPACE" --branch "$GITHUB_SHA" --skip-assets

<<<<<<< HEAD
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "FLUSH PRIVILEGES"

install_whktml() {
    wget -O /tmp/wkhtmltox.tar.xz https://github.com/frappe/wkhtmltopdf/raw/master/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
    tar -xf /tmp/wkhtmltox.tar.xz -C /tmp
    sudo mv /tmp/wkhtmltox/bin/wkhtmltopdf /usr/local/bin/wkhtmltopdf
    sudo chmod o+x /usr/local/bin/wkhtmltopdf
}
install_whktml &

install_site() {
    bench --site test_site reinstall --yes

    if [ "${INSTALL_ERPNEXT}" = "true" ]; then
        bench --verbose --site test_site install-app erpnext crm
    else
        bench --verbose --site test_site install-app crm
    fi

    mkdir -p "${DB_SNAPSHOT}"
    mariadb-dump --host 127.0.0.1 --port 3306 -u root -proot --single-transaction --quick test_frappe | gzip > "${DB_SNAPSHOT}/test_site.sql.gz"
    cp sites/test_site/site_config.json "${DB_SNAPSHOT}/site_config.json"
}

restore_site() {
    cp "${DB_SNAPSHOT}/site_config.json" sites/test_site/site_config.json
    mkdir -p sites/test_site/{public/files,private/files,private/backups,locks,logs}

    db_user=$(python -c "import json; c = json.load(open('sites/test_site/site_config.json')); print(c.get('db_user') or c['db_name'])")
    db_password=$(python -c "import json; print(json.load(open('sites/test_site/site_config.json'))['db_password'])")
    mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE USER IF NOT EXISTS '${db_user}'@'%' IDENTIFIED BY '${db_password}'"
    mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "GRANT ALL PRIVILEGES ON \`test_frappe\`.* TO '${db_user}'@'%'"

    gunzip -c "${DB_SNAPSHOT}/test_site.sql.gz" | mariadb --host 127.0.0.1 --port 3306 -u root -proot test_frappe
}

cd ~/frappe-bench || exit

sed -i 's/watch:/# watch:/g' Procfile
sed -i 's/schedule:/# schedule:/g' Procfile
sed -i 's/socketio:/# socketio:/g' Procfile
sed -i 's/redis_socketio:/# redis_socketio:/g' Procfile

# Server tests never load the built frontend, so skip its yarn install and builds.
YARN_IGNORE_SCRIPTS=true bench get-app --skip-assets crm "${GITHUB_WORKSPACE}"

# Only pull erpnext when the integration is under test, to keep other runs fast.
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    bench get-app --skip-assets erpnext --branch "$(bash "${GITHUB_WORKSPACE}/.github/helper/frappe_ref.sh" "${FRAPPE_BRANCH}" erpnext)"
=======
APPS="frappe whatsapp crm"
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    pilot get-app https://github.com/frappe/erpnext --branch "$FRAPPE_BRANCH" --skip-assets
    APPS="frappe whatsapp erpnext crm"
>>>>>>> 1401ab8 (ci: use pilot with skip-frontend/skip-assets for server tests)
fi

# Start pilot services in background (caller waits on health)
pilot -b "$BENCH_NAME" start > "$RUNNER_TEMP/pilot.log" 2>&1 &
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 1 \
  http://127.0.0.1:7000/api/v1/health

# shellcheck disable=SC2086
pilot new-site test_site --admin-password admin --apps $APPS --skip-assets

<<<<<<< HEAD
bench start &>> ~/frappe-bench/bench_start.log &
CI=Yes bench build --app frappe &
build_pid=$!

if [ -f "${DB_SNAPSHOT}/test_site.sql.gz" ]; then
    restore_site
else
    install_site
fi

# A restored snapshot finishes before the build; tests need its assets.json
wait "$build_pid"
=======
# Emails resolve CSS through assets.json; tests never load the built bundles.
mkdir -p sites/assets && echo '{}' > sites/assets/assets.json

pilot frappe --site test_site set-config allow_tests true
>>>>>>> 1401ab8 (ci: use pilot with skip-frontend/skip-assets for server tests)
