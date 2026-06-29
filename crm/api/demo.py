# Copyright (c) 2024, Frappe Technologies and contributors
# Backward-compatible alias for `crm.api.live_demo`.
#
# This module was renamed from `crm/api/demo.py` to `crm/api/live_demo.py`. The
# login endpoint is referenced by public, externally-bookmarkable URLs (the
# README "Live Demo" link, the live demo site, user bookmarks) as
# `/api/method/crm.api.demo.login`, so we keep this thin re-export to avoid
# breaking those URLs regardless of which app version is deployed.

from crm.api.live_demo import login, validate_reset_password, validate_user
