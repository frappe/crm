# Tiberbu CRM — SPA Theme Overhaul Spec

**Discipline:** BMAD — one story = one vertical slice = one proof; stops at `review`; agents never set `done`; mandatory second-pass; context7-checked (`/frappe/frappe-ui` TOKENS, PHILOSOPHY, COMPONENTS).
**Date:** 2026-07-30
**Trigger:** UX audit — the CRM SPA has 17 identified surfaces where the Tiberbu brand identity (red `#bc1823` / black `#171717` / white) leaks out or is contradicted by hardcoded hex values, raw Tailwind color utilities, or token-system bypasses. The `index.css` remap of `--blue-*` → Tiberbu red is correct and already working; this spec closes the remaining gaps.

**Scope:** Vue 3 SPA only (`frontend/src/`). The www pages (`crm/www/`) were addressed in `tiberbu-crm-centralized-theme-spec.md` and `tiberbu-crm-typography-perf-spec.md` and are out of scope here.

**Constraint:** frappe-ui token system is the source of truth. No new hardcoded hex values. Every fix must resolve through `var(--*)` tokens or frappe-ui Tailwind semantic utilities (`text-ink-*`, `bg-surface-*`, `border-outline-*`). Dark-mode parity is mandatory on every change.

---

## Diagnosis (evidence-based)

The `index.css` token remap successfully covers the primary interactive accent (links, buttons, checkboxes, focus rings, selection). What it cannot cover:

1. **Hardcoded hex / RGB strings in JS-side style bindings** — CSS variable overrides do not reach inline style objects or JavaScript string values.
2. **Raw Tailwind palette utilities** — `text-red-500`, `fill-red-500`, `bg-gray-600`, `bg-gray-900` etc. are not in the `--blue-*` remap chain and bypass it entirely.
3. **SVG `fill` attributes** — `fill="#BC1823"`, `fill="#383838"`, `fill="white"` on SVG elements are not CSS properties and are immune to variable overrides.
4. **Third-party canvas APIs** — Leaflet draw plugin receives color strings; the remap does not affect its rendering.
5. **Public asset `logo.svg`** — `fill="#EF0BF5"` (magenta) is still the app's logo file.

---

## Context7 findings (verified)

- **frappe-ui token system:** semantic category `text-ink-*` (foreground), `bg-surface-*` (background), `border-outline-*` (borders + rings). Numeric step: higher = stronger contrast. Both light and dark values are baked into the CSS variables — a component using `text-ink-gray-7` always gets the correct shade for the active theme. Source: `frappe-ui/skills/frappe-ui/TOKENS.md`.
- **Badge/Button `theme` prop:** allowed values are `"blue" | "red" | "green" | "gray" | "orange"`. The `"blue"` theme is remapped by `index.css` to Tiberbu red. The `"red"` theme resolves through a separate `--red-*` ramp that is NOT remapped — it renders Tailwind red, not brand red. Use `theme="blue"` (remapped) for brand-primary emphasis, NOT `theme="red"`. Source: `Badge.api.md`.
- **Icon color inheritance:** icons should use `fill="currentColor"` / `stroke="currentColor"` to inherit the parent `text-ink-*` class. Source: `frappe-ui/docs/other/icons.md`.
- **Theme philosophy:** `theme` + `variant` are the two color axes. Use `theme="blue"` (remapped) for brand-red CTAs/badges. Use `theme="green"` only for genuine success states (it is intentional, not a violation). Source: `PHILOSOPHY.md`.

---

## Prioritisation

Severity is assessed by visibility × frequency × brand damage:

| ID | Surface | Severity | Reason |
|----|---------|----------|--------|
| THEME-SPA-1 | `logo.svg` magenta `#EF0BF5` | **Critical** | The app's primary logo file shows the pre-rebrand magenta. Visible in Frappe desk header, email footers, system notifications — every authenticated surface. |
| THEME-SPA-2 | Like/favourite icon (`fill-red-500 text-red-500`) — all 6 list views | **High** | Appears in every list view users work in daily. Renders Tailwind red-500 (`#ef4444`), a distinctly different red from brand `#bc1823`. Two competing reds destroy the single-brand-signal principle. |
| THEME-SPA-3 | `FilesUploader` progress ring hardcoded green (`#22C55E`) | **High** | Upload progress appears in email composer, comment box, attachment panels — high-frequency surfaces. Renders green when all other interactive elements are brand red. |
| THEME-SPA-4 | `TaskPriorityIcon` High-priority dot `bg-red-500` | **High** | Same two-reds problem as THEME-SPA-2. High priority = brand red tone, but different enough to clash. |
| THEME-SPA-5 | `AudioPlayer` slider — no dark-mode adaptation | **High** | `background: #fff` thumb + bare `#171717`/`#ededed` JS gradient. Slider thumb disappears in dark mode. Present on every Call Log activity card. |
| THEME-SPA-6 | `CallLogDetailModal` `<audio>` control hardcoded `rgb(237,237,237)` | **High** | Will not invert in dark mode — light gray bar inside a dark modal. |
| THEME-SPA-7 | `CertificateIcon` `fill="#383838"` | **Med** | Hardcoded dark gray, does not adapt to dark mode. Should be `fill="currentColor"`. |
| THEME-SPA-8 | `CRMLogo.vue` `fill="#BC1823"` / `fill="white"` | **Med** | Correct colors today, but immutable to token-level overrides. The white inner glyph could become invisible against certain surfaces. |
| THEME-SPA-9 | `SlaHolidays` custom radio buttons — raw hex | **Med** | `border:#c5c2c2`, `background:white`/`black`/`#171717`/`#525252` etc. Dark mode states partially styled with bare hex. |
| THEME-SPA-10 | Telephony call status text `text-red-700` (Exotel + Avaya) | **Med** | `#b91c1c` — third shade of red on a dark popup, semantically overlapping brand red. |
| THEME-SPA-11 | Calendar default event color string `'green'` | **Med** | New calendar events default to CSS named `green` (#008000) until user changes color. All other event fallbacks are `#bc1823`. |
| THEME-SPA-12 | `Notifications` panel `box-shadow: rgba(0,0,0,0.1)` | **Low** | Minor — raw rgba literal, not a design-token shadow. No visual brand gap but inconsistent. |
| THEME-SPA-13 | `dialog` `theme: 'blue'` string in `DashboardSettings` + `ListBulkActions` | **Low** | Works correctly today (remapped), but the intent string "blue" is semantically wrong for future readers. Change to `theme: 'red'` if frappe-ui ever adds a real `red` CTA theme, or document the remap dependency. |
| THEME-SPA-14 | Tab count badge `bg-gray-600` in Contact/Organization pages | **Low** | Should be `bg-surface-gray-6` to track the token system. |
| THEME-SPA-15 | Hierarchy drag tooltip `bg-gray-900 text-white` | **Low** | Should be `bg-surface-gray-10 text-ink-base`. |
| THEME-SPA-16 | WhatsApp `rgba(238,130,238,0)` gradient endpoint | **Low** | Orphaned orchid/violet CSS color in a gradient stop (transparent endpoint — visually invisible but semantically wrong). |
| THEME-SPA-17 | `DurationIcon` `fill="white"` on clipPath `<rect>` | **Low** | Clip geometry host with explicit `fill="white"` — in dark mode could render as a visible white box. |

---

## UX Assessment

Beyond token hygiene, three UX-layer issues compound the brand inconsistency:

**UX-1 — Two reds confuse signal hierarchy.** The co-existence of brand red (`#bc1823` via token remap) and Tailwind `red-500`/`red-700` (`#ef4444`/`#b91c1c`) means the colour red carries conflicting semantic weight: interactive-brand (intentional) vs. error/priority/warning (inherited Tailwind convention). Users reading a Lead list see their favourite icon in bright `red-500` and the SLA badge in brand red — visually similar but semantically different. Consolidating to a single red resolves this without a redesign: brand red for brand signals, frappe-ui status tokens (`bg-surface-red-*`) for error/danger states.

**UX-2 — Upload progress is invisible as brand interaction.** Every email composer drag-drop and comment attachment shows a green ring. Users learn "green = uploading" not "brand red = system action". After the fix, the upload affordance aligns with every other in-progress state in the app (all brand red).

**UX-3 — Audio player dark mode is a functional regression.** The slider thumb is literally invisible against a dark surface. This is not a brand issue — it is a broken interaction. Call log review (a core sales workflow) is impaired for all dark-mode users.

---

## Stories

### THEME-SPA-1 — Fix `logo.svg` (Critical)

**What:** Replace the magenta `fill="#EF0BF5"` in `crm/public/images/logo.svg` with brand red `#BC1823`, matching `tiberbu-mark.svg`.
Also verify/replace `crm/public/images/logo.png` and the two PWA manifest icons (`manifest-icon-192.maskable.png`, `manifest-icon-512.maskable.png`) — if they carry the magenta mark, regenerate from the corrected SVG.

**Proof:** `grep -n "EF0BF5\|ef0bf5" crm/public/images/logo.svg` returns 0 results. The logo renders brand red in the Frappe desk app header. Screenshot of desk header showing red mark.

---

### THEME-SPA-2 — Consolidate `fill-red-500 / text-red-500` → token (High)

**What:** In all six list views (`LeadsListView`, `DealsListView`, `ContactsListView`, `OrganizationsListView`, `CallLogsListView`, `TasksListView`) the like/favourite icon uses `fill-red-500 text-red-500` for the active/liked state. Replace with frappe-ui semantic utilities that go through the remap:

```diff
- :class="isLiked ? 'fill-red-500 text-red-500' : ''"
+ :class="isLiked ? 'fill-surface-blue-6 text-ink-blue-6' : ''"
```

`--surface-blue-6` resolves to `#bc1823` in light mode and `#d23a41` in dark mode (the correct dark-mode brightened variant already defined in `index.css`). Both are already in the token ramp.

Also address `TaskPriorityIcon` (THEME-SPA-4 same story, same priority):
- `bg-red-500` (High priority) → `bg-surface-blue-6`
- `bg-yellow-500` (Medium) and `bg-surface-gray-4` (Low) are correct semantic choices and untouched

**Proof:** Grep shows zero `fill-red-500\|text-red-500\|bg-red-500` in list view files and `TaskPriorityIcon.vue`. Screenshot of Leads list with a liked lead in both light and dark mode — heart icon renders brand red, not a different tone.

---

### THEME-SPA-3 — FilesUploader progress ring → brand red (High)

**What:** In `FilesUploaderArea.vue` the `CircularProgressBar` component receives `primary: '#22C55E'` (green). Change to the brand red CSS variable value:

```diff
- primary: '#22C55E'
+ primary: 'var(--surface-blue-6, #bc1823)'
```

If `CircularProgressBar` does not accept CSS variable strings (some canvas-based progress bars require a resolved hex), resolve at mount time:

```js
const brandRed = getComputedStyle(document.documentElement)
  .getPropertyValue('--surface-blue-6').trim() || '#bc1823'
```

Pass `brandRed` as the `primary` prop.

**Proof:** Upload a file in the email composer. Progress ring renders brand red. Upload a file in dark mode — ring renders the dark-mode red (`#d23a41`). Screenshot both.

---

### THEME-SPA-5 — AudioPlayer dark-mode fix (High / functional)

**What:** `AudioPlayer.vue` has two issues:

1. `<style scoped>` contains `background: #fff` on the slider thumb and track. Replace with token-aware values:
   ```css
   /* thumb */
   background: var(--surface-base, #fff);
   /* track fill */
   background: var(--surface-blue-6, #bc1823);
   ```

2. The volume gradient string in the component script (`linear-gradient(to right, #171717 N%, #ededed N%)`) — convert to a computed string that reads CSS variables:
   ```js
   const dark = getComputedStyle(el).getPropertyValue('--surface-gray-10').trim() || '#171717'
   const light = getComputedStyle(el).getPropertyValue('--surface-gray-3').trim() || '#ededed'
   // then build the gradient string from dark/light
   ```

**Proof:** Switch to dark mode. Open a Call Log with an audio recording. Scrubber thumb is visible (not white-on-white or invisible). Screenshot light + dark mode of an audio player.

---

### THEME-SPA-6 — CallLogDetailModal native audio control (High)

**What:** In `CallLogDetailModal.vue` the `.audio-control` CSS rule applies `background-color: rgb(237, 237, 237) !important`. This is a hardcoded light gray.

Replace with:
```css
.audio-control {
  background-color: var(--surface-gray-2) !important;
}

[data-theme='dark'] .audio-control {
  background-color: var(--surface-gray-3) !important;
}
```

Note: Native browser `<audio>` controls are heavily UA-styled and the `!important` override may not reach the internal UA shadow DOM on all browsers. Document this limitation in the story. The goal is that the visible container background matches the modal surface in dark mode, even if the UA chrome of the player itself remains UA-styled.

**Proof:** Open a Call Log detail modal in dark mode. The audio control container background matches the dark modal surface (not a floating light gray box). Screenshot.

---

### THEME-SPA-7 — SVG icon `fill` hardcodes → `currentColor` (Medium)

**What:** Three icon components use hardcoded fill values:

1. `CertificateIcon.vue` — `fill="#383838"` → `fill="currentColor"`. Apply a wrapping `class="text-ink-gray-8"` at usage sites (or set on the `<svg>` root) to inherit the correct ink shade.
2. `DurationIcon.vue` — `fill="white"` on the clipPath `<rect>` → `fill="currentColor"`. Since this is a clip geometry path (not a visible shape), it needs `fill="white"` for the clip math to work in SVG. This is a deliberate SVG technical constraint — document it as `<!-- clipPath geometry: fill must be white for SVG clipping to function -->` and leave it. Do NOT change.
3. `CRMLogo.vue` — `fill="#BC1823"` on the outer shape → `fill="var(--surface-blue-6, #BC1823)"`. The inner white glyph `fill="white"` → `fill="var(--surface-base, white)"`. This preserves appearance today but allows token-level overrides later.

**Proof:** `CertificateIcon` in both light and dark modes renders in the correct ink gray (not frozen at `#383838`). `CRMLogo` renders brand red in both modes. Grep confirms no naked `fill="#383838"` or `fill="#BC1823"` remain in these files (except the DurationIcon documented exception).

---

### THEME-SPA-8 — SlaHolidays custom radio buttons → tokens (Medium)

**What:** The custom radio button CSS in `SlaHolidays.vue` has 8 hardcoded color values. Replace each with the corresponding frappe-ui token:

| Old value | Replacement | Role |
|-----------|-------------|------|
| `#c5c2c2` | `var(--outline-gray-3)` | Light mode unchecked ring |
| `black` / `#000` | `var(--surface-gray-10)` | Checked indicator dot + ring |
| `white` / `#fff` | `var(--surface-base)` | Checked and after-pseudo backgrounds |
| `#525252` | `var(--outline-gray-5)` | Dark mode unchecked ring |
| `#171717` | `var(--surface-gray-10)` | Dark mode checked backgrounds |
| `#fff` (dark border) | `var(--outline-gray-1)` | Dark mode checked ring |

**Proof:** Toggle dark mode on the SLA Settings → Holidays page. Radio button checked and unchecked states are visually correct in both modes. Screenshot both.

---

### THEME-SPA-9 — Telephony call status `text-red-700` → token (Medium)

**What:** In `ExotelCallUI.vue` and `AvayaCallUI.vue`, "Call ended" / "No answer" status text uses `text-red-700` (Tailwind `#b91c1c`). Replace with `text-ink-blue-6` (resolves to `#bc1823` / `#e86a70` dark — the brand red).

This status text conveys "call is over" — the same information a red badge would give. Using brand red here unifies the signal.

**Proof:** Simulate a call end/no-answer state in both telephony adapters. Status text renders in brand red (not a third red tone). Verify in light + dark mode.

---

### THEME-SPA-10 — Calendar default event color `'green'` → brand red (Medium)

**What:** In `Calendar.vue` the FullCalendar event color defaults to the CSS named color `'green'`:

```js
color: e.color || 'green'
```

Change to:

```js
color: e.color || '#bc1823'
```

This matches the identical fallback already used in `EventArea.vue`, `EventModal.vue`, `EventNotificationsArea.vue`, and `CalendarEventPanel.vue` — all four already use `'#bc1823'` as the fallback. This story closes the one remaining inconsistency in the same component family.

**Note:** Leaflet draw plugin (`GeolocationControl.vue`) also hardcodes `#bc1823` for shape draw options — this is a Leaflet API constraint (does not accept CSS variables). Document with a comment and leave.

**Proof:** Create a new calendar event without setting a custom color. It renders in brand red, not green. Screenshot.

---

### THEME-SPA-11 — Minor token cleanup: tab badges, drag tooltip, dialog theme strings (Low)

Bundle three low-impact changes into one story:

1. **Tab count badge** (`Contact.vue`, `Organization.vue`, `MobileContact.vue`, `MobileOrganization.vue`):
   `bg-gray-600` → `bg-surface-gray-6`

2. **Hierarchy drag ghost tooltip** (`Hierarchy.vue`):
   `bg-gray-900 text-white` → `bg-surface-gray-10 text-ink-base`

3. **Dialog `theme` strings** (`DashboardSettings.vue`, `ListBulkActions.vue`):
   `theme: 'blue'` → `theme: 'red'`
   Note: frappe-ui Badge/Button `theme` accepts `"blue" | "red" | "green" | "gray" | "orange"` (context7-verified). Since the `index.css` remap maps `--blue-*` to brand red, `theme: 'blue'` *works* today, but `theme: 'red'` is more semantically correct for brand red CTAs. Verify the dialog CTA button still renders brand red after this change.

4. **WhatsApp gradient orphaned color** (`WhatsAppArea.vue`):
   `rgba(238, 130, 238, 0)` (violet/orchid) → `rgba(0, 0, 0, 0)` (neutral transparent endpoint)

**Proof:** Grep shows zero `bg-gray-600`, zero `bg-gray-900 text-white` (in targeted files), `rgba(238` removed from WhatsApp area. Dialog confirm buttons in `DashboardSettings` and bulk actions still render brand red. Tab badges are consistent with the surface gray ramp.

---

## Implementation order

1. THEME-SPA-1 (logo.svg — critical, zero code, just asset replacement)
2. THEME-SPA-5 + THEME-SPA-6 (audio player — functional regressions, unblock dark-mode users)
3. THEME-SPA-2 (like icons — high visibility, all list views, simple class change)
4. THEME-SPA-3 (file upload green ring — high frequency, single component)
5. THEME-SPA-7 → 10 (medium: SVG fills, radio buttons, telephony, calendar)
6. THEME-SPA-11 (low: batch of minor token cleanups)

---

## Proof of completion (overall)

Run after all stories are `review`:

```bash
# Zero raw Tailwind red utilities in component files (excluding index.css):
grep -rn "fill-red-[0-9]\|text-red-[0-9]\|bg-red-[0-9]\|border-red-[0-9]" \
  frontend/src --include="*.vue" --include="*.ts"

# Zero raw Tailwind gray utilities in targeted files:
grep -rn "bg-gray-[0-9]\|text-gray-[0-9]" \
  frontend/src/components/Settings/Hierarchy/Hierarchy.vue \
  frontend/src/pages/Contact.vue \
  frontend/src/pages/Organization.vue

# Zero hardcoded hex strings in .vue/.ts (excluding intentional documented exceptions):
grep -rn "#[0-9a-fA-F]\{3,8\}" frontend/src --include="*.vue" \
  | grep -v "index.css\|Leaflet\|Facebook\|clipPath\|DOCUMENTED"

# Logo is brand red:
grep -c "EF0BF5\|ef0bf5" crm/public/images/logo.svg  # must return 0
grep -c "BC1823\|bc1823" crm/public/images/logo.svg  # must return ≥ 1
```

Browser: switch dark mode toggle. Walk through Leads list → like a lead (brand red heart) → open a Call Log (audio player scrubber visible) → open email composer → upload a file (brand red ring) → open calendar → create event (brand red default). All 6 flows render consistently brand red in both modes.

---

## Risks / notes

- `CertificateIcon.vue` usage sites must apply a `text-ink-*` class wrapper — grep all import sites before changing the icon's fill.
- `theme="green"` on "Won" Deal badge and Twilio "Answer" button are **intentional** semantic status colors (success = green, answer call = green). Do NOT change these — they are correct per the frappe-ui philosophy.
- The `theme="green"` email activity badge in `EmailArea.vue` may be "Sent/Delivered" status — verify semantics before changing. If it is a success state, leave green.
- RSVP attending dots (green/gray/red on CalendarEventPanel) are semantic status signals, not brand identity — leave as-is.
- The `#22C55E` FilesUploader fix requires checking if `CircularProgressBar` accepts CSS variable strings or needs a resolved hex at mount time.
- All changes require `pnpm build` zero warnings + `tsc --noEmit` clean before `review`.
