#!/bin/bash

set -eo pipefail

cd ~ || ex

export BENCH_USE_UV=1

# Frappe (and erpnext) branch to test against; set by CI matrix, defaults to develop.
FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
FRAPPE_REF=$(bash "${GITHUB_WORKSPACE}/.github/helper/frappe_ref.sh" "${FRAPPE_BRANCH}")

# Restored from cache by setup-server-env when the schema is unchanged.
DB_SNAPSHOT="${DB_SNAPSHOT:-$HOME/db-snapshot}"

pip install frappe-bench
[ -d ~/frappe ] || git clone "https://github.com/frappe/frappe" --branch "${FRAPPE_REF}" --depth 1
bench init --skip-assets --frappe-path ~/frappe --python "$(which python)" frappe-bench

mkdir ~/frappe-bench/sites/test_site

cp -r "${GITHUB_WORKSPACE}/.github/helper/site_config.json" ~/frappe-bench/sites/test_site/site_config.json

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL character_set_server = 'utf8mb4'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "SET GLOBAL collation_server = 'utf8mb4_unicode_ci'"

mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE USER 'test_frappe'@'localhost' IDENTIFIED BY 'test_frappe'"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "CREATE DATABASE test_frappe"
mariadb --host 127.0.0.1 --port 3306 -u root -proot -e "GRANT ALL PRIVILEGES ON \`test_frappe\`.* TO 'test_frappe'@'localhost'"

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

<<<<<<< HEAD
bench get-app crm "${GITHUB_WORKSPACE}"

# Only pull erpnext when the integration is under test, to keep other runs fast.
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    bench get-app erpnext --branch "$(bash "${GITHUB_WORKSPACE}/.github/helper/frappe_ref.sh" "${FRAPPE_BRANCH}" erpnext)"
=======
# Server tests never load the built frontend, so skip its yarn install and builds.
bench get-app --skip-assets whatsapp
YARN_IGNORE_SCRIPTS=true bench get-app --skip-assets crm "${GITHUB_WORKSPACE}"

# Only pull erpnext when the integration is under test, to keep other runs fast.
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    bench get-app --skip-assets erpnext --branch "${FRAPPE_BRANCH}"
>>>>>>> 99d6e25 (ci: skip frontend install and asset builds in server tests)
fi

bench setup requirements --dev

bench start &>> ~/frappe-bench/bench_start.log &
CI=Yes bench build --app frappe &

if [ -f "${DB_SNAPSHOT}/test_site.sql.gz" ]; then
    restore_site
else
    install_site
fi
