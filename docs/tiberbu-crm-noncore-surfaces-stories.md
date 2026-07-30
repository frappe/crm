# Tiberbu CRM — Non-Core Surface Stories (glass + brand consistency)

**Date:** 2026-07-30 · **Follows:** `tiberbu-crm-ux-audit.md` (landing/login/unauthorized already done).
**Design contract:** frappe-ui consistency (ink-gray tokens, sentence case, weight ≤800), glass system (blur+saturate, hairline border, one scene device), **red `#bc1823` / black `#171717` / white only**, `www/` Jinja (no build), `@supports`/reduced-motion fallbacks, WCAG AA.

---

## NCS-1 — Public lead/demo form (`crm_form.html`) — HIGHEST VALUE
The landing's primary CTA ("Request a Demo") lands here. Today it's custom-styled but the accent is **black, not Tiberbu red**, and it doesn't match the glass look → jarring drop-off from the polished landing.
- Re-skin to the shared design language: soft red scene behind a **glass form card**, red primary submit, ink-gray labels/text, sentence case, focus rings.
- Keep the existing native Web Form submission engine + field rendering (only restyle).
- **Proof:** screenshot desktop+mobile of the branded form reached via the landing CTA; re-run the round-trip (submit → CRM Lead created) to confirm no functional regression.

## NCS-2 — Form success + error states
The post-submit "thank you" and inline validation currently use the old neutral styling.
- Success: glass confirmation card, red/black accent, sentence case, clear "what happens next" + a path back (to landing or a new submission).
- Error/validation: inline field errors in the semantic error red (kept distinct from brand red), non-jarring.
- **Proof:** screenshot success state (post-submit) + a validation-error state (empty required field).

## NCS-3 — Branded password reset (`www/update-password`)
The login "Forgot password?" link points at **stock Frappe `/update-password`** — an unbranded surface in the middle of a branded auth flow.
- Shadow it with `crm/www/update-password.{py,html}` matching the login card (glass, red, sentence case), POSTing to the **stock** `frappe.core.doctype.user.user.update_password` / reset endpoint — do NOT reimplement the reset logic; only shadow the page. Preserve the `?key=` reset-token flow (the login fix already whitelists `/update-password`).
- Add a route rule if needed; verify the stock reset still completes.
- **Proof:** screenshot; complete a reset-key flow end-to-end (or show the page renders branded with a valid/invalid key and posts to the stock endpoint).

## NCS-4 — Polish audit follow-ups (already-done pages)
Small refinements surfaced in the audit, no new surfaces:
- Landing feature cards: they don't link anywhere — either add `:focus-visible` + subtle affordance or confirm they're intentionally static (drop residual hover cues).
- Mobile trust-strip spacing at <400px; ensure it doesn't wrap awkwardly.
- Sweep decorative SVGs for `aria-hidden`; confirm focus rings on every interactive element across all pages.
- **Proof:** mobile screenshots + a quick keyboard-focus pass.

---

## Order
NCS-1 (drop-off fix) → NCS-2 (same file, states) → NCS-3 (password reset) → NCS-4 (polish sweep).
All stop at `review`; nothing committed. MFA-parity login JS remains untouched.

---

## RESULTS (implemented 2026-07-30) — all `review`

**Red retune (user feedback "red too bright"):** kept the `#bc1823` hex but stopped using it as large fills. The login left panel is now **black-dominant** (`#171717` gradient, matching the SPA sidebar) with red only as a subtle glow accent + red logo/eyebrow/ticks/button. Landing already used restrained red (white bg, small wash, black band). Result: red reads as an accent, not a wash — and it's *more* consistent with the app.

**NCS-1 — Public lead/demo form (`crm_form.html`):** re-skinned from black-accent/flat-gray to the shared design language — soft red scene, glass card, red primary "Request Demo" button, ink-gray labels, red required-asterisks, sentence case, focus rings, `@supports`/reduced-motion fallbacks. Engine untouched. **Round-trip verified:** submit → `CRM-LEAD-2026-00002` created (`source: Web Form`). Proof: `ui-form-desktop.png`, `ui-form-mobile380.png`.

**NCS-2 — Form states:** on-brand success card (red-tint check ring) + a "Back to home" link (non-embed); inline validation in semantic error-red (distinct from brand red). Proof: `ui-form-error.png`, `ui-form-success.png`.

**NCS-3 — Branded password reset (`www/update-password.{py,html}`):** shadows the stock page, POSTs to the **unmodified** `frappe.core.doctype.user.user.update_password` (key or old-password). Matches the login card. **Reset flow verified end-to-end:** fresh key → new password → HTTP 200 → logged into `/crm`. Two bugs found & fixed during build: (1) `frappe.sessions` wasn't resolvable → explicit import; (2) `frappe.form_dict` isn't populated for www GETs → read key from `request.args` + client reads it from the URL (matches stock `get_url_arg`). Proof: `ui-reset.png`.

**NCS-4 — Polish:** `aria-hidden` on all decorative SVGs (landing icons+arrow, login ticks); `:focus-visible` red rings on every interactive element across all 5 pages; mobile spacing verified at 380px (trust strip wraps cleanly). 

**Regression:** login MFA (OTP App) re-tested end-to-end after the red-retune + polish → **PASS**. All surfaces 200/redirect-correct on prod. 2FA test state restored to off. Palette held to red/black/white throughout.

**Surfaces now consistent:** landing, login, unauthorized, lead/demo form, password reset — one glass design language, restrained red, frappe-ui ink-gray tokens, sentence case.
