# Tiberbu CRM — Typography Consistency + Font Performance Spec

**Discipline:** BMAD — one story = one vertical slice = one proof; stops at `review`; agents never set `done`; mandatory second-pass; context7-checked.
**Date:** 2026-07-30 · **Trigger:** user feedback — (a) www typography is "thick / too bold", doesn't match the CRM; (b) even the login page is "extremely slow".
**Scope:** the 5 non-core www surfaces — `login.html`, `index.html`, `access-restricted.html`, `crm_form.html`, `update-password.html`. **Constraint:** red `#bc1823` / black `#171717` / white; `www/` Jinja (no build); MFA-parity login JS untouched.

---

## Diagnosis (evidence, not opinion)

**Typography mismatch — the "too bold":**
- The CRM SPA uses **frappe-ui InterVar** and its heaviest heading is **semibold (600)** — the codebase uses only `-medium` (500) / `-semibold` (600); `font-bold`/700/800/900 essentially never appear on headings.
- context7 (`/frappe/frappe-ui` TOKENS): two scales — `text-*` (tight line-height ~1.15) for headings/labels, `text-p-*` (loose ~1.5–1.6) for prose; **sentence case; distinguish by size/weight/color, not caps.**
- The www pages currently use **`font-weight:800` heroes** and request Google-Fonts weights up to **`900`**. → visibly heavier/blacker than the app. This is the mismatch.

**Slowness — render-blocking web fonts:**
- `login.html` is 28 KB and renders server-side in ~25 ms — the server is not the problem.
- All 5 www pages load **Google Fonts** (`fonts.googleapis.com` CSS → `fonts.gstatic.com`, up to **6 weight files**), cross-origin and **render-blocking** — the browser paints text only after that chain resolves. On a slow or filtered network this stalls first paint badly (the "hustle").
- The SPA does **not** do this — it bundles **InterVar locally** (`crm/public/frontend/assets/Inter.var-*.woff2`, one ~258 KB variable file, same-origin, `Cache-Control: max-age=1yr`). Source of truth: `frappe-ui/src/fonts/Inter/Inter.var.woff2` + `inter.css`.

Both problems have the same fix direction: **stop pulling Inter from Google; serve the same local InterVar the app uses, and cap weights to the app's range.**

---

## Stories

### TYPO-1 — Serve InterVar locally on all www surfaces (kills the slowness)
- Ship the frappe-ui variable font as a static app asset (`crm/public/fonts/Inter.var.woff2`, served at `/assets/crm/fonts/…`, same-origin, long-cache). It's ONE file covering weights 100–900 (variable), vs Google's multi-file chain.
- Add a small shared `@font-face` (InterVar, `font-weight:100 900`, `font-display:swap`) + set `font-family:'InterVar','Inter',…` — inline in each page's `<style>` (no build; Jinja pages can't share a bundle, but the font file is shared/cached across all of them and with the SPA-adjacent origin).
- **Remove** the three Google-Fonts `<link>`s (preconnect ×2 + stylesheet) from all 5 pages.
- **Proof:** page HTML shows zero `fonts.googleapis/gstatic` refs; the woff2 serves `200` `font/woff2` with a long cache header from `/assets/crm/…`; before/after network trace of the login load (blocking cross-origin requests → none). `font-display:swap` = text paints immediately in the fallback, swaps when the (cached) font arrives.

### TYPO-2 — Match the CRM type scale + weights (kills the "too bold")
- **Cap heading weight at 600 (semibold).** Replace every `font-weight:800/900` and `font-weight:700` heading with **600**; body/labels stay 400–500. No heading above 600 anywhere.
- Align sizes/line-heights to frappe-ui's intent: headings tight (~1.15–1.2), prose loose (~1.5). Trim the oversized hero (`clamp(...3.6rem)` at 800) to a lighter, smaller, semibold treatment closer to the app's `text-3xl-semibold`.
- Keep sentence case (already fixed in the audit); ensure no residual uppercase.
- Re-tune letter-spacing that was compensating for the heavy weight.
- **Proof:** grep shows no `font-weight` >600 and no Google-Fonts weight >600 across the 5 pages; side-by-side screenshots (login/landing) reading noticeably lighter, matching an SPA screenshot for weight; MFA login re-tested (login JS untouched).

---

## Notes / risks
- **Fallback:** if the local woff2 ever 404s, `font-family` falls back to system `-apple-system/Segoe UI/sans-serif` — page stays readable (no dependence on Google).
- **Fork-safety:** the font file is an additive asset under `crm/public/`; copying frappe-ui's own font (same file the app already ships) — no submodule edit.
- **Verification includes** a real browser load, not just server timing, since the whole point is client-side render blocking.
- Order: TYPO-1 (perf, unblocks fast iteration) → TYPO-2 (weights). Both `review` only.

---

## RESULTS (implemented 2026-07-30) — `review`

**TYPO-1 — local InterVar, Google Fonts removed (fixes slowness):** copied frappe-ui's variable font to `crm/public/fonts/Inter.var.woff2` (serves `200 font/woff2` same-origin at `/assets/crm/fonts/…`, 1-year cache). Added an inline `@font-face` (InterVar, `100 900`, `font-display:swap`) to all 5 pages and set `font-family:'InterVar','Inter',system…`. Removed the 3 Google-Fonts `<link>`s (2 preconnect + stylesheet) from every page.
  - **Proof:** all 5 pages `google=0, local-fontface=2`. Login load trace: **0 googleapis/gstatic requests**, one same-origin `Inter.var.woff2`, networkidle 830 ms (previously blocked on a cross-origin CSS→woff2 chain). `font-display:swap` = instant text paint.

**TYPO-2 — weights capped at 600 (fixes "too bold"):** every `font-weight:700/800/900` → **600** across all 5 pages (was 4×800 login, 5× index, etc.). Landing hero trimmed `3.6rem`→`3rem` and tracking `-0.03em`→`-0.02em`. Now no heading exceeds the SPA's semibold ceiling.
  - **Proof:** grep shows zero `font-weight >600` on any page; login/landing screenshots read visibly lighter (semibold, not black), matching the CRM app's weight discipline.

**Regression:** login MFA (OTP App) re-tested end-to-end → **PASS**. 2FA test state restored off.

### Notes
- desk.tiberbu.app couldn't be sampled directly (auth-gated, 301) — not needed: frappe-ui *is* the desk's type system, and its rules (local InterVar, ≤600 weight, sentence case, tight/loose scales) were sourced from the installed package + context7 and applied.
- **Recommendation (not done, needs approval):** the SPA login route redirects to these www pages, so consistency is now aligned. If you later want a permanent shared CSS instead of per-page inline `@font-face`, that'd be a small refactor — flagged, not actioned.
