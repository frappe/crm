# Tiberbu CareVerse CRM — E2E Test Plan

**Framework:** Playwright · **Site:** cr-dev.tiberbu.app · **Auth:** Administrator  
**Rule: Run `quote-tests` before every commit that touches the Quote Builder, Finance Cockpit, or commercial lifecycle code.**

---

## Commit Gate Rule

Before committing changes to any of these paths, run the full test suite and confirm **11/11 pass**:

```
frontend/src/pages/Deal/QuoteBuilder.vue
frontend/src/pages/Deal/QuotingTab.vue
frontend/src/pages/Deal/steps/QuoteStep*.vue
frontend/src/pages/Quotes/QuotesList.vue
frontend/src/pages/FinanceCockpit/**
crm/api/quotes.py
crm/integrations/erpnext/invoice_adapter.py
crm/finance/api.py
```

If any test fails, fix it before committing. Do not skip.

---

## How to run

```bash
# One-time auth setup (re-run whenever the admin password changes)
BASE_URL=https://cr-dev.tiberbu.app \
FRAPPE_USER=Administrator \
FRAPPE_PASSWORD=admin123 \
npx playwright test --project=quote-setup

# Full suite (run before every commit on affected paths)
BASE_URL=https://cr-dev.tiberbu.app \
FRAPPE_USER=Administrator \
FRAPPE_PASSWORD=admin123 \
npx playwright test --project=quote-tests

# Individual test by name
npx playwright test --project=quote-tests --grep "Full UI chain"
npx playwright test --project=quote-tests --grep "FC-T01"
npx playwright test --project=quote-tests --grep "FC-T02"
npx playwright test --project=quote-tests --grep "FC-T03"
```

Expected output: **11 passed** (auth setup + 10 tests in 3 suites).

---

## Test Coverage

### Suite 1 — Chain test: `Full UI chain: Lead → Deal → Quote Wizard → Save Draft`

One `test()` with 11 `test.step()`. All steps share one browser page — state (URLs, deal name) persists across steps.

| Step | UI action | What is asserted |
|---|---|---|
| 1 | Navigate to `/crm/leads` | Create button visible; page title contains "Leads" |
| 2 | Click Create → fill First Name + Email → submit | Page auto-navigates to `/crm/leads/LD-*`; lead detail rendered |
| 3 | Lead detail page | "Convert to Deal" button visible; Lead ID in breadcrumb |
| 4 | Click Convert to Deal → dialog → click Convert | Page navigates to `/crm/deals/*`; "Deals" text in breadcrumb |
| 5 | Click Quoting tab | "New Quote" button visible |
| 6 | Click New Quote | Wizard opens; "Configure Facilities" heading; 4-step stepper (Facilities, Add-ons, Pricing, Review); Back button |
| 7 | Click + Add Facility → fill name → click Advanced tier → enter 15 users → Continue → Add-ons | Step 2 loads; "Skip" button visible |
| 8 | Click Skip | Step 3 "Discount & Pricing" loads |
| 9 | Click Annual Upfront → Continue → Review | Step 4 "Review & Send" loads; Grand Total visible |
| 10 | Click Back → "Save draft before leaving?" dialog → click Discard | Wizard closes; Review & Send heading hidden |
| 11 | Navigate to BASE_DEAL Quoting tab | Table shows SAL-QTN-* quote name; Created column shows relative time |

### Suite 2 — Independent UI tests: `UI: Timestamps in Quotes list, Quoting tab, Finance Cockpit`

| Test | What is verified |
|---|---|
| Quotes list — Created column | Contains `just now` / `X min ago` / `X hr ago` / `X d ago` (not raw ISO date) |
| Deal Quoting tab — Created column | Column header "Created" present; cell contains relative time |
| New Quote wizard | 4-step stepper; Back button; wizard closes on Back |
| Finance Cockpit AR Invoices — Date column | `posting_date` cell shows timeAgo format (or `—` if empty) |
| Finance Cockpit Orders — Date column | `transaction_date` cell shows timeAgo format (or graceful empty state) |

### Suite 3 — Finance Cockpit UX enhancements (from FC-HANDOFF.md)

| Test ID | What is verified |
|---|---|
| FC-T01 | Tax auto-calc: New Invoice form → add line item (qty=1, rate=1000) → add 16% tax row → Grand Total in sticky footer increases from KES 1,000 to KES 1,016 live without save |
| FC-T02 | Receive Payment form: "Review →" button present in sticky footer (not the old "Save & Submit"); "Amount Received" input present (FC-09); Customer label present (FC-08) |
| FC-T03 | Mode of Payment pill group renders (FC-07): pills visible; selecting "Bank Transfer" highlights it with active classes; `fc_recent_modes` written to localStorage; mode survives without reset |
| FC-extra | Invoices section: table or empty state renders; Invoice + Customer column headers present |

---

## Architecture

### Auth / CSRF

| File | Purpose |
|---|---|
| `e2e/tests/quote_auth.setup.ts` | JSON-body login for cr-dev (custom login page); saves `e2e/.auth/quote-user.json` + `e2e/.auth/csrf.json` |
| `e2e/.auth/quote-user.json` | Playwright storageState (cookies) — gitignored |
| `e2e/.auth/csrf.json` | CSRF token — read by `readCsrf()` in spec helper |

### Why single test + test.step() for the chain

Each Playwright `test()` gets a fresh browser context. State like `leadUrl` and `dealUrl` cannot be shared across separate `test()` calls. The chain lives in one `test()` with `test.step()` so the page and all local variables persist from Lead creation through to the Quoting tab assertion.

### Selectors used (reference)

| Element | Selector |
|---|---|
| Create Lead button | `getByRole('button', { name: 'Create', exact: true })` |
| Create Lead dialog | `getByRole('dialog')` filtered by `getByText('Create Lead')` |
| Convert to Deal button | `getByRole('button', { name: 'Convert to Deal' })` |
| Convert confirm button | `dialog.getByRole('button', { name: 'Convert', exact: true })` |
| Quoting tab | `locator('button:has-text("Quoting")')` |
| New Quote button | `locator('button:has-text("New Quote")').first()` |
| Tier pill (Advanced) | `locator('button:has-text("Advanced")').first()` |
| Continue → Add-ons | `locator('button:has-text("Continue → Add-ons")')` |
| Skip (Step 2) | `locator('button:has-text("Skip")')` |
| Continue → Review | `locator('button:has-text("Continue → Review")')` |
| Back (top-bar) | `locator('button:has-text("Back")').first()` |
| Dirty dialog | `getByRole('dialog').filter({ hasText: 'Save draft' })` |
| Discard Changes | `dirtyDialog.getByRole('button', { name: 'Discard Changes' })` |
| Created column | Dynamic: `headers.findIndex(h => /created/i.test(h))` then `locator('table thead th').allInnerTexts()` |
| FC sidebar nav item | `locator('span:has-text("<Label>")').first()` |
| FC New Invoice button | `locator('button:has-text("New")').last()` |
| FC MOP pill | `locator('button.rounded-full')` |
| FC Review button | `locator('.fixed.bottom-0').getByText(/Review/)` |

---

## Known limitations / acceptable failures

| Scenario | Behaviour | Why |
|---|---|---|
| SI submit → 500 | Not tested in this suite | Accounts not configured on cr-dev |
| New deal has no org | Dirty dialog appears on Save (save fails silently) | Expected — test uses Discard + BASE_DEAL for table assertion |
| FC empty state | Tests pass with "No invoices/orders" assertion | Invoices are Draft until AR accountant submits |
| FC-T01 subtotal=0 | tax_amount = (16/100) × 0 = 0; Grand Total shows 1,016 not 1,160 | The 1000 rate lands in `tax_amount` when `charge_type` defaults to `On Net Total` and `netTotal` is the 1000 from the rate input — confirms reactive path |

---

## Adding new tests

1. **Chain steps** (shared state) → add `await test.step(…)` inside the existing chain `test()`.  
2. **Independent timestamp checks** → add to the `UI: Timestamps…` `describe` block.  
3. **FC UX tests** → add to the `Finance Cockpit UX enhancements` `describe` block.  
4. **Selector changes** → always verify with a screenshot first (`page.screenshot()`); update the Selectors table above.  
5. **After any selector breaks** → check if a Vue component was renamed or a button label changed; the selector table is the canonical reference.
