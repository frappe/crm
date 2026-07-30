# E1-S4 — Hardcoded-Hex Sweep

**Story:** E1-S4 · Re-hue off-brand hardcoded accents for brand consistency; preserve semantic status colors.
**Status:** review · **Date:** 2026-07-30 · **Build:** `yarn build` ✓

---

## Method

`grep -rEn '#[0-9a-fA-F]{3,8}' frontend/src` (excluding the E1-S1 token file `index.css`),
then classified each hit: **re-hue** off-brand decorative accents to the Tiberbu red
ramp; **preserve** semantic status colors, neutrals (black/white/gray = on-brand), and
third-party brand marks.

## Re-hued (off-brand → Tiberbu red)

| File | Was | Now | Note |
|---|---|---|---|
| `components/Controls/RatingInput.vue` | yellow ramp (`#eab308`/`#fde68a`/`#fcd34d`) | red ramp (`#bc1823`/`#ee9499`/`#e15b62`; dark `#e0545a`/`#f6c2c5`/`#d23a41`) | filled/preview/removing stars; `--rating-empty` stays neutral gray (`#d1d5db` light / `#4b5563` dark) |
| `components/Controls/GeolocationControl.vue` (×2) | `#4f46e5` (indigo) | `#bc1823` | Leaflet draw polyline/polygon color |
| `components/EventNotificationsArea.vue` | `#30A66D` | `#bc1823` | default event color fallback |
| `components/Modals/EventModal.vue` | `#30A66D` | `#bc1823` | default event color fallback |
| `components/Activities/EventArea.vue` | `#30A66D` | `#bc1823` | default event color fallback |
| `components/Calendar/CalendarEventPanel.vue` (×2) | `#30A66D` | `#bc1823` | default event color fallback |
| `components/Settings/ThemeSwitcher.vue` (×12) | macOS traffic-light dots `#FF5F57`/`#FEBC2D`/`#28C840` | `bg-gray-300` | decorative window-chrome dots neutralized to monochrome |

Note on event-color defaults: these are only the *fallback* when a user hasn't chosen a
color (`event.color || '#bc1823'`). User-picked colors are unaffected.

## Preserved (with rationale)

| File | Hex | Why kept |
|---|---|---|
| `components/FilesUploader/FilesUploaderArea.vue` | `#22C55E` | **Semantic success** — the upload-progress ring, paired with `text-ink-green-5`. Keeping success-green distinct from brand-red preserves WCAG-legible status semantics (per spec: "keep error-red distinct from brand-red"). |
| `components/Icons/FacebookIcon.vue` | `#0866ff` | **Third-party brand** — Facebook's official logo blue; recoloring it would be incorrect. |
| `components/Settings/Sla/SlaHolidays.vue` | `#000`/`#fff`/`#171717`/`#525252`/`#c5c2c2` | **Neutrals** — black/white/gray IS the Tiberbu palette; already has explicit light/dark values. |
| `components/Activities/AudioPlayer.vue` | `#171717`/`#ededed`/`#fff` | **Neutrals** — scrubber gradient mirrors `--surface-gray-10/3`; on-brand black/white. |
| `components/Activities/EmailContent.vue` | `#ededed`/`#e2e2e2`/`#343434`/`#424242` | **Neutrals** — sandboxed email-body surface grays, both themes defined. |
| `components/Icons/CertificateIcon.vue` | `#383838` | Neutral dark-gray icon fill. |
| `components/Icons/CRMLogo.vue` | `#BC1823` | Already Tiberbu red (E1-S2). |
| `components/Controls/RatingInput.vue` | `#d1d5db`/`#4b5563` | `--rating-empty` — intentional neutral for unfilled stars. |

## Dependency-owned defaults (NOT app code — out of scope, fork-safety)

Two off-brand hexes survive in the **built** bundle but have **zero occurrences in
`frontend/src`** — they originate in the `frappe-ui` submodule (a git submodule; editing
it violates the hard fork-safety constraint):

- `#30A66D` — `frappe-ui/src/components/Calendar/useEventBase.ts` (frappe-ui's own event default)
- `#4f46e5` — `frappe-ui/src/components/TextEditor/extensions/shared/color-utils.ts`

These are only reachable via frappe-ui internals we don't render off-brand in practice
(our app-level event fallbacks now pass `#bc1823`). Left untouched deliberately; revisit
only if frappe-ui exposes a theming prop for them.

## Verification

- `cd frontend && yarn build` → ✓ built (pre-existing chunk-size + brace-expansion
  plugin warnings only; none from these changes).
- Built bundle: `FF5F57` traffic-dot hex → **0 occurrences** (removed); `bc1823`/`e0545a`
  present. `30A66D`/`4f46e5` remaining hits trace to the frappe-ui submodule (above).
- App regression (light + dark): `/tmp/crm-proof/s4-app-light.png`, `s4-app-dark.png` —
  brand red throughout, no blue/indigo/green accents, no dark/light regression.
- Component proof (rating stars + dots, light + dark): `/tmp/crm-proof/s4-components.png`
  — red filled stars, neutral empty stars readable on both themes; dots monochrome.

## Watch-out (not in scope)

The onboarding card still reads "Welcome to Frappe CRM" (a translatable UI string, not a
color). Brand-name copy replacement is separate from the hex sweep; flag for a future
i18n/copy pass if desired.
