# Tiberbu CRM — Centralized Theme + Login Layout Fix Spec

**Discipline:** BMAD — one story = one slice = one proof; stops at `review`; second-pass; **context7-checked** (done: `/frappe/frappe-ui` TOKENS).
**Date:** 2026-07-30 · **Triggers:** (1) "prefer centralized theme tokens consistent with the CRM"; (2) "sample desk.tiberbu.app" — done; (3) login has "jumbled/disorganized text" — reproduced; (4) "keep red, not deep red" — hold `#bc1823`; (5) spec first.

---

## Evidence gathered

**desk.tiberbu.app sampled** (Host-header, guest 200): runs `careverse_hq`. Its `/` + `/login` are *marketing* pages — Google Fonts, hero `font-weight:800`, hardcoded hex (`--text-primary:#262626`). The desk **app** (frappe-ui SPA) is the opposite: local InterVar, heading weight ≤ semibold, semantic `ink-*` tokens.
→ User chose **frappe-ui tokens + local InterVar** as the source of truth (CRM-consistent), not the careverse marketing hardcodes. Use careverse only as *layout/taste* inspiration, not token source.

**Exact CRM token values** (from the built CRM `index-*.css`, frappe-ui oklch, pure-neutral — NOT blue-tinted like my earlier `#1f272e`):
| token | light value | role |
|---|---|---|
| `--ink-gray-9` | `oklch(.168 0 0)` (#171717-ish) | primary text / headings |
| `--ink-gray-8` | `oklch(.205 0 0)` | strong text |
| `--ink-gray-7` | `oklch(.341 0 0)` | secondary text |
| `--ink-gray-6` | `oklch(.439 0 0)` | muted labels |
| `--ink-gray-5` | `oklch(.58 0 0)` | faint / placeholder |
| `--outline-gray-2` | `oklch(.913 0 0)` | hairline borders |
| `--surface-gray-2` | ~`oklch(.964 0 0)` | subtle page bg |

**context7 (frappe-ui) rules:** InterVar; two scales — `text-*` tight LH **1.15** for headings/labels, `text-p-*` loose **1.5–1.6** for prose; 11px→24px+; **sentence case, never uppercase; distinguish by size/weight/color.**

**Login jumble — reproduced** (measured at 1366×768, 1440×900, 1536×864): the left panel uses `justify-content:center` for the hero block **plus** an absolutely-positioned `.l-foot`. When hero+lead+3 value-points are tall, they run **past the fold** (lead line "…unified around" clips) and the value points collide with the footer (both at y≈891–906 in a 768 viewport). This is the disorganized text.

---

## Design decisions (locked)

- **Color:** keep **bright `#bc1823`** as `--brand` (NOT deep/maroon). Retain the black-dominant login panel (it matches the SPA `#171717` sidebar) with red as accent — that's structural black, not "deep red."
- **Tokens:** centralize on frappe-ui's pure-neutral `ink-gray` (oklch) + local InterVar. Replace the ad-hoc blue-tinted `#1f272e/#4c5257/#667075` with the real oklch neutrals.
- **Weight:** headings **semibold 600 max** (matches the CRM app the user works in daily; the user said "too bold"). Marketing landing hero may sit at 600 too — refined over punchy — consistent with the app.
- **Line-height:** headings 1.15–1.2 (tight), prose 1.5–1.6 (loose), per context7.

---

## Stories

### THEME-1 — Centralized brand stylesheet (single source of truth)
Create `crm/public/css/tiberbu-brand.css` (served at `/assets/crm/css/tiberbu-brand.css`) holding:
- `@font-face` InterVar (local `/assets/crm/fonts/Inter.var.woff2`, `font-display:swap`).
- `:root` tokens: `--brand:#bc1823`, `--brand-dark` (a hover shade, still red not maroon), the frappe-ui `--ink-gray-9…5` (oklch neutrals), `--outline-gray-2`, `--surface` bg, radii, glass vars, `--focus`, `--font`.
- Shared primitives so pages stop re-declaring: `.t-h1/.t-h2/.t-label/.t-muted` type helpers (weight ≤600, correct LH), `:where(a,button,input,...):focus-visible` ring, `prefers-reduced-motion` + `@supports` backdrop fallbacks.
**Proof:** file serves `200 text/css`; contains the oklch tokens + local font; grep shows bright `#bc1823` (no maroon).

### THEME-2 — Fix the login left-panel layout jumble
Rework the `.left` panel so content **never clips or overlaps** at any viewport:
- Use a single flow (flex column) with the footer **in-flow** (not absolute) OR give the centered block `min-height:0; overflow` safety + move footer into the column; guarantee eyebrow→hero→lead→points→footer stack with real gaps and bottom padding.
- Ensure it holds at 1366×768 (the failing case), 1440×900, 1536×864, and mobile (panel hidden).
**Proof:** measured bounding boxes show **no overlap** and everything within the viewport (or scrolls cleanly) at all four sizes; screenshots.

### THEME-3 — Adopt the shared theme across all 5 www pages
Point `login/index/access-restricted/crm_form/update-password` at `tiberbu-brand.css` (`<link rel="stylesheet">`), delete the now-duplicated `:root`/`@font-face`/weight declarations from each page's inline `<style>` (keep only page-specific layout). Re-tune any remaining ink colors to the oklch tokens.
**Proof:** each page links the shared css; per-page inline token blocks removed; grep shows no `font-weight>600`, no Google Fonts, no blue-tinted grays; all 5 render identically-themed; **login MFA re-tested (JS untouched)**; load trace still 0 cross-origin font requests.

---

## Risks / notes
- www pages can't import a Vite bundle, but a **static CSS `<link>` from `crm/public/`** is the correct "centralized" mechanism for Jinja pages — one file, cached across all pages, single source of truth. This is as close to the SPA's token system as www allows without a build.
- oklch is supported in all current evergreen browsers; provide a hex fallback comment for each token in the css.
- Fork-safety: all additive under `crm/public/` + `www/`; no submodule edits.
- Order: THEME-1 (tokens) → THEME-2 (layout bug) → THEME-3 (adopt + cleanup). All `review`.

---

## RESULTS (implemented 2026-07-30) — `review`

**THEME-1 — centralized stylesheet:** `crm/public/css/tiberbu-brand.css` (serves 200 `text/css`) — frappe-ui pure-neutral `ink-gray` oklch tokens (from the CRM's own built CSS), local InterVar `@font-face`, bright `--brand:#bc1823` (no maroon), shared `.t-*` type/`.t-card`/focus/fallback primitives.

**THEME-2 — login jumble fixed:** reworked `.left` to an in-flow 3-row flex column (`height:100vh` shell, `overflow-y:auto` safety). Verified no clip / no overlap / no page-scroll at 1280×720, 1366×768, 1440×900, 1536×864, 1920×1080 (the 1366 case that was broken now clean).

**THEME-3 — adoption:** all 5 www pages `<link>` the shared css; per-page inline `@font-face` + duplicated token blocks removed. Verified per page: `link=1, google=0, inline-fontface=0, font-weight>600 = 0`. Load trace: **0 Google-Font requests**, one same-origin `Inter.var.woff2`, `tiberbu-brand.css` cached across pages.

**Typography:** headings capped at semibold 600 (matches the frappe-ui CRM app, per user "too bold"). desk.tiberbu.app sampled: its careverse marketing pages use 800 + Google Fonts + hardcoded hex — deliberately NOT copied; used only as layout inspiration.

**Login left-panel photo (user request):** added a subtle healthcare stock photo behind a heavy dark scrim.
- Source: Unsplash `photo-1576091160399-112ba8d25d1d` (doctor w/ stethoscope), Unsplash License (free, commercial-ok, no attribution required).
- Processed to `crm/public/images/login-bg.jpg` (900×1200, desaturated 0.72 + darkened, 53 KB progressive). Layered under the black + red gradients at ~90% scrim so text/red dominate and stay WCAG-legible.

**Regression:** login MFA (OTP App) re-tested end-to-end → **PASS**. Test user `sales.tester@tiberbu.test` had to be recreated (a `bench migrate` had pruned it + the demo Web Form; both restored). 2FA state restored off. All surfaces healthy on prod.
