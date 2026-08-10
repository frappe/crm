# Finance Cockpit UX Enhancement — Handoff

**Repo:** `/home/ubuntu/frappe-bench/apps/crm`
**Site:** `cr-dev.tiberbu.app` · password `admin123`
**Spec:** `docs/FC-UIUX-STORIES.md` — authoritative source, read first
**Test plan:** `e2e/TEST_PLAN.md` — run `quote-tests` before every commit

---

## Current state (audit)

### Files to change

```
frontend/src/pages/FinanceCockpit/components/crud/LineItemsGrid.vue
frontend/src/pages/FinanceCockpit/components/crud/FinanceForm.vue
frontend/src/pages/FinanceCockpit/components/crud/FinanceDetail.vue
frontend/src/pages/FinanceCockpit/components/crud/PaymentAllocationForm.vue
frontend/src/pages/FinanceCockpit/components/crud/SummaryBar.vue
frontend/src/pages/FinanceCockpit/components/crud/FieldRenderer.vue
frontend/src/pages/FinanceCockpit/constants/formLayouts.js
```

### Key gaps (confirmed by code audit)

1. `LineItemsGrid` in taxes mode receives no `qtyField`/`rateField`/`amountField` — entering a tax `rate` % does nothing. `tax_amount` is manually typed. Grand Total in the sticky footer is wrong until save.
2. `PaymentAllocationForm` renders Mode of Payment as a native `<select>`. Mode is reset to empty on every customer change — almost always wrong (line 231).
3. Customer Combobox searches only `name` (code), not `customer_name` (display name).
4. No `paid_amount` input — user must select invoices first, total appears in footer. Direction is inverted.
5. `SummaryBar.vue` uses raw `text-gray-*` / `bg-gray-*` instead of design-system tokens — dark mode breaks.
6. Detail view summary strip picks the first 5 scalar fields positionally — wrong fields for Sales Invoice.
7. `FieldRenderer` renders currency fields as bare number inputs — no symbol prefix, no formatting.

---

## Implementation order

### P0 — Broken, no dependencies

#### FC-01 · Tax rate % → `tax_amount` auto-computation
**Files:** `LineItemsGrid.vue`, `FinanceForm.vue`

Pass `netTotal` prop from `FinanceForm` into the taxes `LineItemsGrid`.
In `updateCell`, when `fieldname === 'rate'` is updated on a tax row:

```js
if (!props.amountField && props.netTotal > 0) {
  updated['tax_amount'] = (value / 100) * props.netTotal
}
```

Only fires for rows where `charge_type === 'On Net Total'`.
`charge_type === 'Actual'` rows stay fully manual.

#### FC-03 · Grand Total live update
**Files:** no extra changes beyond FC-01

`FinanceForm` already has a `taxTotal` computed at line 183 that sums `tax_amount` across tax rows. Once FC-01 writes `tax_amount` reactively, `taxTotal` and `grandTotal` update automatically. No separate work needed.

#### FC-07 · Mode of Payment — pill group, not `<select>`
**File:** `PaymentAllocationForm.vue`

Replace `FormControl type="select"` for `modeOfPayment` with a horizontal pill group:

```
[ Cash ]  [ Bank Transfer ]  [ M-Pesa ]  [ Cheque ]  [ + More ▾ ]
```

- Top 4 pills from `localStorage('fc_recent_modes')`, fallback to `['Cash', 'Bank Transfer']`
- Selecting a pill stores it in recency and sets `modeOfPayment`
- `+ More` opens a Combobox searching the `Mode of Payment` doctype
- **Delete line 231** — the `modeOfPayment = ''` reset on customer change

---

### P1 — Significant friction

#### FC-08 · Customer smart search
**File:** `PaymentAllocationForm.vue`

Add `or_filters` to search both `name` and `customer_name`:

```js
params.or_filters = JSON.stringify([
  ['name', 'like', `%${query}%`],
  ['customer_name', 'like', `%${query}%`],
])
```

After selection, show an inline balance chip:
```
[ Kenyatta National Hospital  × ]   KES 4.2M outstanding (3 invoices)
```
Fetch balance from `crm.finance.api.get_ar_invoices` filtered by customer.

#### FC-09 · Amount Received input + Auto-Allocate
**File:** `PaymentAllocationForm.vue`

Add a `paid_amount` `ref(null)` input above the invoice table.
When customer + amount are both set, show an "Auto-Allocate" button.
Auto-allocation fills invoices sorted by `due_date asc` until the amount is exhausted.
Footer shows: `Allocated KES X | Unallocated KES Y | Total KES Z`.

#### FC-04 · Currency inputs — symbol prefix in edit mode
**File:** `FieldRenderer.vue`

For `fieldtype === 'currency'` in edit mode, wrap the `FormControl` in a flex row with a non-editable badge:

```html
<div class="flex items-center gap-1.5">
  <span class="text-xs font-medium text-ink-gray-5 w-8 text-right">{{ currency }}</span>
  <FormControl type="number" ... />
</div>
```

`currency` prop is already passed down from `FinanceForm → FieldRenderer`.

#### FC-10 · Invoice table — sort, Select All, overdue treatment
**File:** `PaymentAllocationForm.vue`

- Clickable column headers for Due Date, Outstanding, Invoice — toggle asc/desc, show ▲/▼
- Default sort: `due_date asc` (oldest due first)
- Select All header checkbox: checks all rows at full outstanding amount
- Overdue rows: **text color only** — `due_date` cell gets `text-red-500 dark:text-red-400`
  plus an inline pill `Overdue Xd` beside the date. No border rails. No background tints.

#### FC-11 · Payment review step before submit
**File:** `PaymentAllocationForm.vue`

Replace the "Record Payment" button with "Review →".
Clicking slides in a read-only review panel (in-place transition, not a modal):

```
Customer      Kenyatta National Hospital
Amount        KES 2,200,000
Mode          Bank Transfer
Reference     TIB-20260810-001
Date          10 Aug 2026

Allocations
  ACC-SINV-2026-00014    KES 1,500,000
  ACC-SINV-2026-00013      KES 700,000

Unallocated   KES 0

[ ← Back to Edit ]   [ Confirm & Post ]
```

Errors from the backend are displayed inline in the review panel — not as auto-dismissing toasts.
Success state shows the Payment Entry name: `PE-2026-00001 posted` + "View in Accounts →" link.

#### FC-05 · Item rate auto-lookup from price list
**Files:** `LineItemsGrid.vue`, `FieldRenderer.vue`

When `item_code` changes in a line item row, fetch:
```
GET /api/resource/Item Price
  ?filters=[["item_code","=","<code>"],["price_list","=","<selling_price_list>"]]
  &fields=["price_list_rate"]&limit=1
```
Auto-fill `rate` and `item_name` if found.
If not found: inline hint "No price on Standard Selling" — `rate` stays editable.
Changing `selling_price_list` in the invoice header re-fetches all item prices.

#### FC-06 · Item name column in line items
**File:** `formLayouts.js`

Add `item_name` as a Data column after `item_code` in the Sales Invoice items table.
Auto-filled by FC-05, user-editable override. Hidden on mobile.

#### FC-13 · Detail summary strip — explicit fields
**File:** `formLayouts.js`

Define the Sales Invoice summary strip explicitly instead of positional first-5:

```js
summaryFields: ['customer', 'grand_total', 'status', 'due_date', 'outstanding_amount']
```

Add "X days overdue" sub-label below due_date when `due_date < today && docstatus === 1`.
Show "Paid in Full" in green when `outstanding_amount === 0`.

#### FC-14 · Related document links on detail view
**File:** `FinanceDetail.vue`

Add a "Related" panel at the bottom of the detail view.

For Sales Invoice:
- `crm_deal` → "View Deal →" link to `/crm/deals/:dealId`
- `crm_quotation` → "View Quote →" link
- Payment Entries linked to this invoice

For Payment Entry:
- Invoices from `references` child table as link chips

---

### P2 — Polish

#### FC-15 · SummaryBar design token alignment
**File:** `SummaryBar.vue`

| Replace | With |
|---|---|
| `text-gray-500` | `text-ink-gray-5` |
| `text-gray-700` | `text-ink-gray-7` |
| `text-gray-900` | `text-ink-gray-9` |
| `border-gray-200` | `border-outline-gray-2` |
| `bg-gray-50` | `bg-surface-gray-1` |
| `bg-gray-800/50` | `bg-surface-blue-6` (Grand Total row — use brand accent) |

#### FC-16 · Tax breakdown in SummaryBar
**File:** `SummaryBar.vue`

When `taxes.length > 1`, expand the Tax line into individual rows.
Single tax row: collapsed as before. Zero-amount rows hidden.

#### FC-12 · Reference labels adapt to payment mode
**File:** `PaymentAllocationForm.vue`

```js
const REF_LABELS = {
  'Bank Transfer': ['Bank Reference / RTGS Ref', 'Value Date'],
  'M-Pesa':        ['M-Pesa Transaction ID',      'Transaction Date'],
  'Cheque':        ['Cheque Number',               'Cheque Date'],
  'Cash':          [null, null],  // hide both fields
}
```

Cash mode: Reference No and Reference Date fields hidden and not required.

#### FC-02 · Tax template picker
**Files:** `FinanceForm.vue`, `formLayouts.js`

"Apply Tax Template" button in the Taxes section header.
Combobox searches `Sales Taxes and Charges Template` filtered by `company`.
Selecting a template replaces the `taxes` array and triggers FC-01 recalculation.

---

## Design constraints

> These are hard rules. Do not deviate.

- **No colored border rails on cards or rows.** Convey overdue/status via text color, inline badges, or pills only. No `border-l-4 border-red-*` patterns.
- **No drawers or modals for primary work.** Full-page views only. FC-11 review step is an in-place panel transition.
- **Token discipline.** Use `text-ink-gray-*`, `bg-surface-*`, `border-outline-gray-*`. Zero raw `text-gray-*` / `bg-gray-*` in new or modified code.
- **Frappe v15 backward compatibility.** Verify any API or DocType feature in v15 before using it. Flag v16-only APIs as blockers.
- **Run tests before every commit** on affected paths:

```bash
BASE_URL=https://cr-dev.tiberbu.app \
FRAPPE_USER=Administrator \
FRAPPE_PASSWORD=admin123 \
npx playwright test --project=quote-tests
```

Expected: **7/7 passed**.

---

## Tests to write alongside implementation

| ID | What to test |
|---|---|
| FC-T01 | Tax auto-calc: enter rate 16 → `tax_amount = subtotal × 0.16` → Grand Total updates live without save |
| FC-T02 | Full payment click-path: find submitted SI → Receive Payment → enter amount → auto-allocate → select mode pill → Review → Confirm → verify SI `outstanding_amount = 0` |
| FC-T03 | Mode of Payment pill persists across customer change and page reload (localStorage) |

---

## Run command reference

```bash
# Build frontend
cd /home/ubuntu/frappe-bench/apps/crm/frontend && npm run build

# Restart workers after Python changes
cd /home/ubuntu/frappe-bench && bench restart

# Run migrate after any patch or doctype change
cd /home/ubuntu/frappe-bench && bench --site cr-dev.tiberbu.app migrate

# Run tests
BASE_URL=https://cr-dev.tiberbu.app \
FRAPPE_USER=Administrator \
FRAPPE_PASSWORD=admin123 \
npx playwright test --project=quote-tests
```
