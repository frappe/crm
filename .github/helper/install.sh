#!/bin/bash

set -eo pipefail

# Pilot-based backend test setup. Server tests never serve web pages,
# so frontend work is skipped entirely (prebuilt frappe assets only).
# Mirrors frappe/suite#1181 and frappe/pilot#744.

FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
PILOT_VERSION="v0.0.99-pre-alpha"
BENCH_NAME="frappe-bench"
BENCH_PATH="$HOME/pilot/benches/$BENCH_NAME"

export PATH="$HOME/pilot/bin:$HOME/.local/bin:$PATH"

curl -fsSL "https://raw.githubusercontent.com/frappe/pilot/${PILOT_VERSION}/install.sh" | sh -s -- --version "$PILOT_VERSION"

pilot new "$BENCH_NAME" --frappe-branch "$FRAPPE_BRANCH"
pilot -b "$BENCH_NAME" init --skip-frontend

BENCH_DIR="$BENCH_PATH"
cd "$BENCH_DIR"

# uv is used by pilot/suite CI for the test extras
uv pip install --python env/bin/python -e "apps/frappe[test]"

# Server tests never load the built frontend, so skip asset setup.
pilot get-app https://github.com/frappe/whatsapp --skip-assets
pilot get-app "$GITHUB_WORKSPACE" --branch "$GITHUB_SHA" --skip-assets

APPS="frappe whatsapp crm"
if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    pilot get-app https://github.com/frappe/erpnext --branch "$FRAPPE_BRANCH" --skip-assets
    APPS="frappe whatsapp erpnext crm"
fi

# Start pilot services in background (caller waits on health)
pilot -b "$BENCH_NAME" start > "$RUNNER_TEMP/pilot.log" 2>&1 &
curl --fail --silent --show-error --retry 30 --retry-connrefused --retry-delay 1 \
  http://127.0.0.1:7000/api/v1/health

# shellcheck disable=SC2086
pilot new-site test_site --admin-password admin --apps $APPS --skip-assets

# Emails resolve CSS through assets.json; tests never load the built bundles.
mkdir -p sites/assets && echo '{}' > sites/assets/assets.json

pilot frappe --site test_site set-config allow_tests true
