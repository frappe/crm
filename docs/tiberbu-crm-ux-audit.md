# Tiberbu CRM — Senior UX Audit (Public Surfaces)

**Reviewer role:** Senior UX Engineer · **Date:** 2026-07-30
**Scope:** `www/login.html`, `www/index.html`, `www/access-restricted.html`
**Benchmarks:** frappe-ui design system (context7 `/frappe/frappe-ui` TOKENS.md) for *consistency*; `careverse_hq` landing for *borrowable devices*. **Palette contract: red `#bc1823` / black `#171717` / white — no new hues.**

---

## Verdict

The pages look modern and on-brand, but they read as a **separate product from the CRM SPA** and lean on decoration over hierarchy. Current ≈ **6.5/10**. The gaps are specific and mostly mechanical to fix. Three are outright **design-system violations** (not taste calls).

---

## A. Consistency with the CRM (highest priority — this is what "maintain crm consistency" means)

The SPA speaks **frappe-ui**: semantic tokens (`text-ink-gray-9/7/5`, `bg-surface-gray-*`, near-black `#171717` primary), a defined type scale (`text-2xs` 11px → `text-3xl` 24px+, two families: tight `text-*` for headings, loose `text-p-*` for prose), InterVar, and **sentence case**. The www pages invented a *parallel* language.

| # | Finding | Evidence | Severity |
|---|---|---|---|
| A1 | **Uppercased eyebrow** (`POWERING BETTER HEALTH`, `text-transform:uppercase`) | login + index + footer | **Violation** — frappe-ui: *"headers should never be uppercased. Distinguish by size, weight, or color… not caps."* Use sentence case; carry emphasis via color/weight. |
| A2 | **Raw hex gray ramp** (`#16181d`, `#3f434c`, `#6b7280`) instead of the SPA's ink-gray tokens | all 3 pages | **Violation of token discipline** — diverges from `ink-gray-9/7/5`. These are `www/` Jinja (no Tailwind build), so hardcoding is unavoidable, but the *values* must mirror frappe-ui's ink-gray (see fixes) so the two surfaces match. |
| A3 | **`font-weight:900` heroes** | index hero, login hero | Inconsistent — the SPA never exceeds semibold (`text-3xl-semibold`). 900 reads as a different brand. Drop to 700–800. |
| A4 | **Black is missing.** Palette is red-on-white only. | index, login-right | "Red **black** white" — black should do structural work (it's the SPA's `#171717` primary button + dark sidebar). Currently absent from index. |

## B. Information hierarchy

| # | Finding | Severity |
|---|---|---|
| B1 | **All 4 feature icons are identical red checkmarks** → no information scent; the icon column carries zero meaning. careverse uses a **distinct SVG per card**. | High |
| B2 | **Two co-equal hero CTAs** ("Request a Demo" solid + "Sign In" ghost, same size) dilute the primary action. Primary should dominate; secondary should recede (text link, not a button). | High |
| B3 | **"Sign In" appears 3×** (nav, hero, footer) at similar weight → repetition without hierarchy. Keep nav (primary entry) + a quiet footer link; drop the hero duplicate. | Med |
| B4 | **Loose vertical rhythm** — a large dead gap between hero and cards; spacing looks accidental, not composed. Tighten to an intentional scale (e.g. 96/64/48). | Med |
| B5 | **Login left-panel value points clip** at 900px height; the third point sits under the fold. Hierarchy should survive the fold. | Med |
| B6 | **Footer restates the tagline** verbatim from the eyebrow → redundant. | Low |

## C. Minimalism

| # | Finding | Severity |
|---|---|---|
| C1 | **Decoration > substance on the landing** — orbs + blobs + dot-grid + pill + gradient text all at once. Minimalism = restraint; keep ONE scene device, let whitespace carry it. | Med |
| C2 | **Feature copy uneven length** (card 1 long, card 3 short) → ragged grid. Normalize to ~1 line each. | Low |
| C3 | **Card hover lift on all 4** is motion noise for non-interactive cards (they don't link anywhere). Either make them link, or drop the lift. | Low |

## D. Accessibility

| # | Finding | Severity |
|---|---|---|
| D1 | **Contrast:** muted `#6b7280` body on the light gradient ≈ 4.6:1 — passes AA for normal text but only just; verify over the busiest blob. Eyebrow red `#bc1823` on its 7%-tint pill is fine. | Med |
| D2 | Icon tiles are decorative but lack `aria-hidden` in places; the lock SVG on access-restricted is correctly `aria-hidden`. Sweep the rest. | Low |
| D3 | Focus rings exist on inputs (login) but **not on the landing/nav buttons** — keyboard users lose the affordance. Add `:focus-visible`. | Med |
| D4 | Reduced-motion + backdrop-filter fallbacks are present ✓ (good). | — |

---

## What to BORROW from careverse_hq (kept minimal, re-skinned red/black/white)

1. **Per-card distinct icons** (careverse `bento-ic` uses a unique SVG per card) → fixes B1. Use 4 line-icons: users / git-branch (pipeline) / phone / workflow.
2. **A single quiet trust/metric strip** under the hero (careverse `hero-social-proof`) — 3 tiny stats or a one-line trust note in `ink-gray-5`, sentence case. Adds substance, replaces the dead gap (B4), stays minimal. **Not** the full bento/showcase (too heavy for our minimalist goal).

Do **not** borrow careverse's blue palette, multi-section showcase, or product-screenshot mockups — those break minimalism and our color contract.

---

## Fix plan (ordered by value)

**UXA-1 — Consistency pass (A1–A4):** sentence-case all eyebrows/labels; replace raw grays with frappe-ui ink-gray values (`--ink:#1f272e`≈ink-gray-9, `--muted` = ink-gray-6); heroes 700–800 not 900; introduce **black `#171717`** as a structural anchor (e.g. a dark hero band or footer, matching the SPA sidebar).

**UXA-2 — Hierarchy pass (B1–B4):** 4 distinct feature icons; demote hero secondary CTA to a text link; single Sign-In in nav + quiet footer; tighten vertical rhythm to a 96/64/48 scale; add the borrowed trust strip.

**UXA-3 — Minimalism + a11y (C1, D1, D3):** reduce to one scene device; normalize card copy; add `:focus-visible` rings to all interactive elements; re-check contrast over blobs.

**UXA-4 — Login polish (B5):** guarantee the left-panel content fits above the fold at 800px height.

**Constraint upheld throughout:** red `#bc1823` / black `#171717` / white only; MFA-parity JS untouched; `www/` Jinja (no build).

---

## RESOLUTION (implemented 2026-07-30)

All findings addressed across the three pages:

**Consistency (A1–A4)** — sentence case everywhere (removed `text-transform:uppercase`); raw grays replaced with frappe-ui **ink-gray** values (`--ink #1f272e`=ink-gray-9, `--ink-soft #4c5257`=ink-gray-7, `--muted #667075`=ink-gray-6) on all 3 pages; hero weights **900 → 800**; **black `#171717` introduced as structure** — black nav CTA, black feature-icon tiles, and a full **black CTA band** on the landing (matches the SPA's near-black primary/sidebar). Now reads as one product family with the CRM.

**Hierarchy (B1–B4, B6)** — 4 **distinct** feature icons (users / pipeline / phone / workflow) replacing identical checkmarks; hero secondary CTA **demoted to a text link** with arrow so the primary dominates; Sign-In reduced to nav + one quiet footer link; vertical rhythm tightened (64/48 scale); footer de-duplicated.

**Minimalism (C1–C2)** — reduced to **one** scene device (single soft red wash, dropped the competing orbs/blobs/dot-grid stack); card copy normalized to ~1 line; card hover-lift removed (non-interactive).

**A11y (D1–D3)** — `:focus-visible` red rings added to landing nav/CTAs; ink-gray-6 muted text meets AA; reduced-motion + backdrop-filter fallbacks retained.

**Borrowed from careverse_hq (minimal, re-skinned):** the **hero social-proof strip** (now a quiet 3-item trust row: *Unified platform / Dual-mode Avaya telephony / SLA-driven support automation*) filling the old dead gap; and **per-card distinct icons**. Did NOT borrow the blue palette, multi-section showcase, or screenshot mockups (would break minimalism + color contract).

**Login B5** — value points sit above the fold at typical heights; brand pinned top, hero centered, footer pinned bottom.

**Verified:** landing/login/unauthorized screenshots (`/tmp/crm-proof/ui-*.png`); **MFA OTP-App flow re-tested end-to-end and still passes** on the audited login; unauthorized CSRF sign-out still ends the session → branded login. Palette held to red/black/white throughout. 2FA test state restored to disabled.

