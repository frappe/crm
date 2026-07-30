# E1-S3 — Runtime Brand (FCRM Settings)

**Story:** E1-S3 · Set runtime brand (`FCRM Settings` brand_name/logo/favicon = Tiberbu CRM) + document it.
**Status:** review · **Date:** 2026-07-30 · **Site:** `cr-dev.tiberbu.app`

---

## What this is

`FCRM Settings` is a **Single** DocType. The Vue SPA reads it once at load
(`frontend/src/stores/settings.js` → `createDocumentResource` → `setupBrand()`),
exposing a reactive `brand = { name, logo, favicon }`. Those three values drive:

| Field        | Surfaced in                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `brand_name` | Left-sidebar app label — `UserDropdown.vue` `{{ brand.name \|\| 'CRM' }}`     |
| `brand_logo` | Sidebar mark — `BrandLogo.vue` (`<img :src="brand.logo">`, falls back to `CRMLogo.vue`) |
| `favicon`    | Browser-tab icon — `usePageMeta(() => ({ title, icon: brand.favicon }))` across all page views |

This is **runtime site data**, not a code change — there is nothing to build or
commit for the values themselves. The re-hued brand tokens (E1-S1) and the red
`CRMLogo.vue` fallback (E1-S2) already ship in the frontend; E1-S3 populates the
DB so the configured brand name/logo/favicon replace the generic "CRM" defaults.

## Applied values (cr-dev)

```
brand_name = "Tiberbu CRM"
brand_logo = /files/tiberbu-logo.png      (public File, 512×512, #BC1823 mark)
favicon    = /files/tiberbu-favicon.png   (public File, 128×128, #BC1823 mark)
```

## Brand assets

Source PNGs live at `docs/brand/` (additive, fork-safe — no core edit):

- `docs/brand/tiberbu-logo.png` — 512×512, sidebar logo
- `docs/brand/tiberbu-favicon.png` — 128×128, browser-tab favicon

Both are rendered from the exact red mark in
`frontend/src/components/Icons/CRMLogo.vue` (rounded square `#BC1823` + white
glyph), so the runtime logo matches the SPA's built-in fallback pixel-for-pixel.
Rendered via headless Chromium (`/tmp/render-brand.mjs`) since
rsvg/cairosvg/ImageMagick are absent on this host. Replace with the official
Tiberbu SVG when brand delivers it (BRD watch-out: canonical hex confirmation).

## Reproduce on a fresh site

Files are uploaded as **public** File records (so the SPA and browser tab can
fetch them without auth), then the three fields are set with the v16-correct
Single API. `frappe.db.set_value(single, None, ...)` is removed in v15+; use
`set_single_value` (context7-verified against `/frappe/frappe` version-16
`database/database.py`).

```python
# bench --site <site> console
import frappe, os
frappe.set_user("Administrator")

def upload(path):
    with open(path, "rb") as f:
        content = f.read()
    f = frappe.get_doc({
        "doctype": "File",
        "file_name": os.path.basename(path),
        "attached_to_doctype": "FCRM Settings",
        "attached_to_name": "FCRM Settings",
        # NOTE: no attached_to_field — avoids File.on_update taking the legacy
        # set_value path against a Single (unsupported in v15+).
        "is_private": 0,
        "content": content,
    })
    f.save(ignore_permissions=True)
    return f.file_url

base = frappe.get_app_path("crm", "..", "docs", "brand")
logo = upload(os.path.join(base, "tiberbu-logo.png"))
fav  = upload(os.path.join(base, "tiberbu-favicon.png"))

frappe.db.set_single_value("FCRM Settings", {
    "brand_name": "Tiberbu CRM",
    "brand_logo": logo,
    "favicon": fav,
})
frappe.db.commit()
```

Or, in production, an admin can set the same three fields through the SPA:
**Settings → Brand Settings** (`frontend/src/components/Settings/BrandSettings.vue`).

## Proof

- Sidebar, light mode: `/tmp/crm-proof/brand-light-sidebar.png` — red mark + "Tiberbu CRM".
- Sidebar, dark mode: `/tmp/crm-proof/brand-dark-sidebar.png` — same, on `#171717` base (parity holds).
- Tab title `"Leads - List"`, `link[rel~=icon].href → /files/tiberbu-favicon.png`, `body` contains "Tiberbu" (both themes).
- `/files/tiberbu-logo.png` and `/files/tiberbu-favicon.png` both serve `200 image/png`.
