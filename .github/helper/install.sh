#!/bin/bash

# Provision-only: prepares the cached Pilot bench (framework + dependency apps
# + dependency-only site). The app under test is installed per-run afterwards,
# so cached runs always test fresh PR code. Run `save` (actions/cache) after
# this on a cache miss, before anything installs crm.
#
# Expects from the caller: FRAPPE_BRANCH, INSTALL_ERPNEXT, PILOT_CACHE_HIT
# ("true" when the bench was restored, anything else provisions from scratch).

set -eo pipefail

FRAPPE_BRANCH="${FRAPPE_BRANCH:-develop}"
BENCH_NAME="frappe-bench"
BENCH_PATH="$HOME/pilot/benches/$BENCH_NAME"
PILOT_CACHE_HIT="${PILOT_CACHE_HIT:-}"

export PATH="$HOME/pilot/bin:$HOME/.local/bin:$PATH"
printf '%s\n' "$HOME/pilot/bin" "$HOME/.local/bin" >> "$GITHUB_PATH"
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

curl -fsSL "https://raw.githubusercontent.com/frappe/pilot/develop/install.sh" | sh

if [ ! -d "$BENCH_PATH" ]; then
  pilot new "$BENCH_NAME" --frappe-branch "$FRAPPE_BRANCH"
  pilot -b "$BENCH_NAME" set-bench-config admin_allow_site_to_pilot_communication false
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
  APPS="frappe whatsapp"
  if [ "${INSTALL_ERPNEXT}" = "true" ]; then
    APPS="frappe whatsapp erpnext"
  fi
  # shellcheck disable=SC2086
  pilot new-site test_site --admin-password admin --apps $APPS --skip-assets
  # Emails resolve CSS through assets.json; tests never load the built bundles.
  mkdir -p sites/assets && echo '{}' > sites/assets/assets.json
  # Stop MariaDB so the cache gets a consistent data directory.
  systemctl --user stop pilot-mariadb.service
fi
