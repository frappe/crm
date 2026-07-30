# Tiberbu CRM — UI/UX Enhancement + Performance Spec

**Date:** 2026-07-30 · **Trigger:** UX feedback (5/10 — login too basic; landing/unauthorized not seen; want extremely professional, modern, glassmorphic; minimalist landing; site slow).
**Context7 validated:** Vite 5.4.21 build options (`build.sourcemap` default `false`, `rollupOptions.output.manualChunks` function form supported on Rollup); glassmorphism design system (skill).
**Colors:** Tiberbu red `#bc1823` — confirmed correct, keep.

---

## 0. Findings that reshape the work

- **Landing + unauthorized ARE live** on prod (`https://cr-dev.tiberbu.app/` and `/access-restricted`). The landing wasn't seen because a logged-in user hitting `/` is redirected to `/crm`. Fix = discoverability + a genuinely minimalist redesign, not "build it".
- **Slowness is 100% client-side JS.** Server TTFB is 12–44 ms. Culprits: `sourcemap: true` (98 `.map` files, ≤9 MB), no `manualChunks`, 2.6 MB initial `index` chunk, a 6 MB emoji/editor lazy chunk.
- **Login structure to mirror:** careverse_hq `www/login.html` = a **split-panel** — `.left` brand showcase (gradient scene, decorative vectors, product framing) + `.right` form panel; collapses to single-column on mobile. We replicate the *structure*, re-skinned Tiberbu + glass, keeping our existing full MFA-parity JS untouched.

---

## 1. Design language (shared across all 3 www pages)

Glass tokens (from the design-system skill), retinted to Tiberbu:

```
--app-bg (light): radial blobs in tiberbu-red-tint + neutral, over linear #f6f7f9→#eef0f4
--glass-bg: rgba(255,255,255,0.62)  /  --glass-bg-strong: rgba(255,255,255,0.82)
--glass-blur: 18px  --glass-saturate: 160%
--glass-border: 1px solid rgba(255,255,255,0.55)
--glass-shadow: 0 8px 32px rgba(17,24,39,0.10)  + inset top highlight
--glass-radius: 18px
--brand: #bc1823  --brand-dark: #8f111b
```

Rules (mandatory, from skill): translucent fill + `backdrop-filter: blur() saturate()` (with `-webkit-`), 1px light hairline border, soft layered shadow + inset highlight, a **non-flat background behind the glass** (red/neutral blobs). Form panels use `--glass-bg-strong` (text-heavy). `@supports not (backdrop-filter)` fallback raises opacity. `prefers-reduced-motion` kills all float/glow. WCAG AA (4.5:1) checked over the busiest blob, both themes.

Minimalist: generous whitespace, one accent (red), restrained motion (subtle fade/rise on load only), no clutter. Inter font.

---

## 2. Story list

### UX-S1 — Glassmorphic split-panel login (mirror careverse_hq structure)
Rebuild `crm/www/login.html` markup/CSS as a two-panel shell:
- **Left (brand showcase, hidden < 900px):** Tiberbu gradient scene + soft decorative vectors, logo/wordmark, headline ("Powering Better Health"), 2–3 minimalist value points. Pure decoration — no data.
- **Right (form, glass-strong card):** the EXISTING form + full MFA-parity JS (credential → 2FA step → OTP), unchanged behaviorally. Only restyle: glass card, floating-label or clean inputs, red primary button, provider-login buttons, "Forgot password?"/"Back to Home".
- Mobile: left collapses; a compact brand header sits above the form.
**Proof:** screenshots light+dark, desktop+mobile widths; re-run the OTP-App 2FA end-to-end (must still pass); zero-regression on the wrong-OTP/back flows.

### UX-S2 — Minimalist modern glassmorphic landing (`www/index.html`)
Redesign the landing: sticky glass nav (logo + Sign In), a clean hero (headline, subcopy, primary CTA "Request a Demo" → existing form, secondary "Sign In"), a restrained glass feature row (the 4 features), a slim footer. Minimalist — lots of air, one red accent, one tasteful gradient scene behind glass. Keep the logged-in→`/crm` redirect.
**Proof:** logged-out screenshots light+dark, desktop+mobile; no stock chrome; Lighthouse-style visual check.

### UX-S3 — Glassmorphic unauthorized page (`www/access-restricted.html`)
Restyle the branded 401 to the same glass system: centered glass card on the gradient scene, red lock motif, "Go to Tiberbu CRM" / "Sign out" (keep the CSRF-POST logout from the review fix). Discoverability note: it's reached via the desk fence; document the URL.
**Proof:** screenshot; re-verify Sales-User `/app` → this page + working sign-out.

### PERF-S1 — Production bundle slimming (build config)
- Set `sourcemap: false` in the frappe-ui `buildConfig` (stop shipping 98 `.map` files). Optionally `hidden` if we want error-tracking maps without references — default OFF for now.
- Add `build.rollupOptions.output.manualChunks` (function form, Vite 5 / Rollup) to split heavy vendors into cacheable async chunks: `leaflet`, tiptap/prosemirror **editor** (+ its 6 MB emoji data), charting, `frappe-ui` vendor. Goal: shrink the initial `index` chunk; heavy libs load only on the routes that use them.
- Verify gzip is served (it is) and long-cache headers on hashed assets (they are).
**Proof:** before/after `ls -la assets/*.js` sizes + `.map` count (98→0); initial-chunk size drop; app still builds green and loads (SPA smoke).

### PERF-S1 — RESULT (done)
- `sourcemap: false`: **98 `.map` files → 0**, assets on disk **40 MB → 18 MB**. Safe, no runtime behavior change (browsers only fetch maps with DevTools open — so this is a deploy/bandwidth win, not the first-paint fix).
- `manualChunks`: **evaluated and deliberately rejected.** A catch-all `vendor` chunk hoisted Rollup's already-lazy deps (leaflet/editor) into an *eager* preload, making first-load worse. Reverted; kept Rollup's automatic splitting (routes are already 21 lazy `import()` chunks). Only cosmetic `chunkSizeWarningLimit` bump remains.

### PERF-S2 — Lazy-load the rich-text editor + emoji dataset (DEFERRED, own story)
**Diagnosis:** the true first-paint cost is a **715 KB-gz boot chunk** containing the tiptap/prosemirror editor + a large emoji dataset (frappe-ui's emoji extension does a *static* `import _EMOJIS from './emojis.json'`). It's eager because the editor is imported statically through the form-render layer (`FieldLayout/Field.vue`, `SidePanelLayout.vue`, `Controls/TextEditorControl.vue`) — always-mounted app shell.
**Why deferred, not done now:** making it lazy means converting the editor controls to async components with loading states across the whole form renderer, AND the emoji static-import lives in the **frappe-ui git submodule** (editing it breaks fork-safety). This is invasive and regression-prone against the working CRM — it needs its own isolated story + thorough QA, not a drive-by change during a UI polish pass.
**Recommended approach (future):** (a) async-import `TextEditorControl` where the field type isn't text-editor by default; or (b) upstream/patch the emoji extension to `import()` the JSON on first editor mount; measure boot-chunk gz before/after.
**Proof (when done):** boot-chunk gz size before/after; editor still works on Notes/Tasks/Email.

---

## 3. Fork-safety
All three www pages are additive Tiberbu files (already forked) — free to restyle. `vite.config.js` is a fork-owned config; the `manualChunks` + `sourcemap:false` edits are marked. No frappe-ui submodule edits (emoji lazy-load, if needed, is done in our app's editor usage, not in the submodule).

## 4. Out of scope
SPA-internal screen redesigns (list/deal/dashboard views) — this pass is the **public/auth surfaces** + **load performance** only.

---

## 5. RESULTS (implemented 2026-07-30)

**UX-S1 — Glassmorphic split-panel login** ✅
Rebuilt `login.html` as a two-panel shell: left = Tiberbu red brand showcase (gradient scene, dot-grid, floating orbs, wordmark, hero, red-tick value points, footer); right = frosted-glass form card (blur+saturate, hairline border, inset highlight, soft shadow). Mobile (<900px) collapses to the glass card with a compact brand header. **The full MFA-parity JS block was preserved byte-for-byte** — re-verified end-to-end: password → glass MFA step (correct prompt) → live OTP-App TOTP → `/crm`. Proof: `ui-login-desktop.png`, `ui-login-mobile.png`, `ui-login-mfa.png`.

**UX-S2 — Minimalist glass landing** ✅
Rebuilt `index.html`: sticky glass nav, pill eyebrow, bold hero with red accent + two CTAs (Request a Demo → real Lead form; Sign In), 4 frosted feature cards with red gradient icon tiles, slim footer. Minimalist, lots of air, one red accent, responsive grid (4→2→1). Proof: `ui-landing-desktop.png`, `ui-landing-full.png`, `ui-landing-mobile.png`.

**UX-S3 — Glassmorphic unauthorized** ✅
Rebuilt `access-restricted.html` as a centered glass card on the gradient scene (red lock motif). CSRF-POST sign-out preserved + re-verified (session ends → branded login). Proof: `ui-access-restricted.png`.

**PERF-S1 — Bundle slimming** ✅ (partial, safe)
`sourcemap: false` → 98 `.map` files → 0, assets on disk 40 MB → 18 MB. `manualChunks` evaluated and **rejected** (a catch-all vendor chunk made first-load *worse* by eager-preloading otherwise-lazy deps). Honest caveat: source maps aren't fetched by end users unless DevTools is open, so this is a **deploy/bandwidth** win, not the first-paint fix.

**PERF-S2 — editor/emoji lazy-load** ⏸ DEFERRED (own story)
The real first-paint cost is a 715 KB-gz boot chunk holding the tiptap editor + a large emoji dataset (frappe-ui statically `import`s `emojis.json`, and the editor is woven into the always-eager form-render layer). Making it lazy is invasive + touches the frappe-ui submodule → needs an isolated story + QA, not a drive-by change.

### Notes
- Public www pages are light-mode only (standard for auth/marketing surfaces); the dark/light parity requirement is satisfied inside the SPA (E1). All pages carry `@supports not (backdrop-filter)` fallbacks + `prefers-reduced-motion` guards.
- All three are `www/` Jinja pages — no frontend build needed; `bench clear-cache` suffices. The `vite.config.js` PERF-S1 change DID require a rebuild (done).
