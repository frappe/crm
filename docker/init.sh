#!/bin/bash

# Ensure MariaDB client does not enforce TLS over TCP when connecting to MariaDB 10.8 server
if [ ! -f ~/.my.cnf ] || ! grep -q "skip-ssl" ~/.my.cnf 2>/dev/null; then
    printf '\n[client]\nssl=0\nskip-ssl\n' >> ~/.my.cnf 2>/dev/null || true
fi
if [ -w /etc/mysql/mariadb.cnf ] 2>/dev/null; then
    if ! grep -q "skip-ssl" /etc/mysql/mariadb.cnf 2>/dev/null; then
        printf '\n[client]\nssl=0\nskip-ssl\n' >> /etc/mysql/mariadb.cnf 2>/dev/null || true
    fi
fi

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
    bench start
    exit 0
else
    echo "Creating new bench..."
fi

bench init --skip-redis-config-generation frappe-bench --version version-15

cd frappe-bench

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

bench get-app crm --branch main

bench new-site crm.localhost \
    --force \
    --mariadb-root-password 123 \
    --admin-password admin \
    --no-mariadb-socket

bench --site crm.localhost install-app crm
bench --site crm.localhost set-config developer_mode 1
bench --site crm.localhost set-config mute_emails 1
bench --site crm.localhost set-config server_script_enabled 1
bench --site crm.localhost clear-cache
bench use crm.localhost

# Register custom Lead List Script if present
if [ -f /workspace/lead_list_script.js ]; then
    /home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init('crm.localhost')
frappe.connect()
with open('/workspace/lead_list_script.js', 'r', encoding='utf-8') as f:
    script_content = f.read()
if not frappe.db.exists('CRM Form Script', 'CRM Lead List Customizations'):
    doc = frappe.get_doc({
        'doctype': 'CRM Form Script',
        'name': 'CRM Lead List Customizations',
        'dt': 'CRM Lead',
        'view': 'List',
        'enabled': 1,
        'script': script_content
    })
    doc.insert()
    frappe.db.commit()
"
fi

bench start