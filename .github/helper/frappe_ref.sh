#!/bin/bash
# Resolve a version-NN branch to its latest release tag; other refs pass through.
# Usage: frappe_ref.sh <ref> [repo]   e.g. frappe_ref.sh version-16 erpnext

set -euo pipefail

ref="$1"
repo="${2:-frappe}"

if [[ "$ref" =~ ^version-([0-9]+)$ ]]; then
	major="${BASH_REMATCH[1]}"
	ref=$(git ls-remote --tags --refs "https://github.com/frappe/${repo}" "v${major}.*" |
		sed 's#.*refs/tags/##' | grep -E "^v${major}\.[0-9]+\.[0-9]+$" | sort -V | tail -1 || true)
fi

[ -n "$ref" ] || { echo "No release found for $1 in frappe/${repo}" >&2; exit 1; }
echo "$ref"
