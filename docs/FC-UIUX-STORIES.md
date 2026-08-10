# Finance Cockpit — UX Enhancement Stories
**Scope:** Sales Invoice edit surfaces · Tax computation · Component hydration · Payment flow  
**Priority order:** P0 = broken/data-loss · P1 = significant friction · P2 = polish

---

## Epic 1 — Sales Invoice: Live Tax Computation

### FC-01 · Tax Rate → Amount Auto-Calculation  `P0`

**Problem today:**  
The "Taxes & Charges" section renders a `rate` column (the %) and a `tax_amount` column (the KES value). Entering 16 in `rate` does nothing — `tax_amount` stays at whatever the user last typed. The user must calculate and enter the amount manually. The SummaryBar shows a "Tax" line summed from these manually-entered values, so it is always wrong until the user does arithmetic.

**Desired behaviour:**  
When the user changes `rate` (%) in any tax row, `tax_amount` recomputes immediately:

```
tax_amount = net_total × (rate / 100)
```

Where `net_total` is the current items subtotal (qty × rate across all line items).

When the user adds or changes a line item (qty or rate), all existing tax rows with a `charge_type` of `"On Net Total"` recalculate simultaneously.

**Acceptance criteria:**
- Typing "16" in the Rate column of a tax row immediately updates tax_amount to `net_total × 0.16`
- Changing item qty or rate triggers re-derivation of all "On Net Total" tax rows
- The SummaryBar Grand Total updates within the same render cycle — no stale flash
- Manually overriding a `tax_amount` (user types a custom value) marks that row with a small "custom" indicator and stops auto-deriving until rate is edited again
- Rows with `charge_type = "Actual"` are never auto-derived — they remain fully manual
- `charge_type = "On Previous Row Total"` derives from the cumulative total of preceding rows

**What to build:**  
In `LineItemsGrid.vue`: when `props.amountField` is absent (taxes mode), add a `taxAmtField` prop and a separate `netTotal` prop. In `updateCell`, when `fieldname === 'rate'` and `props.netTotal > 0`:
```js
updated['tax_amount'] = (value / 100) * props.netTotal
```
Pass `netTotal = subtotal` from `FinanceForm` into the taxes `LineItemsGrid`.

---

### FC-02 · Taxes & Charges Template Picker  `P1`

**Problem today:**  
There is no way to apply a pre-configured tax template in one action. Users must manually add each tax row, fill `account_head`, type `rate`, and wait for FC-01 to compute the amount. This is 4+ steps per tax component.

**Desired behaviour:**  
A "Apply Tax Template" button above the taxes table. Clicking it opens a compact picker (Combobox, searchable, shows template name + rate summary). Selecting a template replaces the entire `taxes` array with the template's rows, pre-filling `charge_type`, `account_head`, `rate`, and computing `tax_amount` via FC-01 logic.

**Acceptance criteria:**
- Button appears in the Taxes section header when `!readOnly`
- Template Combobox searches `Sales Taxes and Charges Template` filtered by `company`
- After selection, existing tax rows are replaced — a confirmation toast says "VAT 16% applied (2 tax rows)"
- Clearing the template (× on the picker) removes all tax rows after a confirmation
- Template application triggers FC-01 recalculation immediately

---

### FC-03 · Grand Total Live Update Without Page Reload  `P0`

**Problem today:**  
`subtotal`, `taxTotal`, `grandTotal` are client-side computed from the `reactive` doc — this is architecturally correct. But `taxTotal` is currently summed from `lineItem[taxAmountField]` where `taxAmountField = 'tax_amount'` — a field that is only written when the user manually types, not when FC-01 auto-derives it (because FC-01 hasn't been built yet). Result: the Grand Total in the sticky footer is wrong until save.

**Desired behaviour:**  
The sticky footer shows the correct Grand Total at every keystroke. The computation chain is:

```
items subtotal  = Σ (qty × rate) across all item rows
tax total       = Σ tax_amount across all tax rows  [updated by FC-01]
grand total     = items subtotal + tax total
```

No save required to see the correct total. The SummaryBar and the sticky footer both reflect the same value, updated synchronously.

**Acceptance criteria:**
- Adding an item row (with qty and rate) immediately updates the footer Grand Total
- Changing qty or rate updates Grand Total within the current input event cycle
- Deleting an item row reduces the Grand Total immediately
- Tax changes (FC-01) cascade into Grand Total within the same cycle
- On a fresh invoice with no rows: footer shows "KES 0" not blank/null
- Currency symbol is derived from `doc.currency` — changing currency does not re-fetch rates but does update the symbol in the footer

---

### FC-04 · Currency Inputs: Symbol and Formatting in Edit Mode  `P1`

**Problem today:**  
`FieldRenderer` renders currency fields as `FormControl type="number"` — a bare number input. No currency prefix (KES / $), no thousands separator, no right-alignment. In read-only mode `formatCurrency()` is applied correctly; in edit mode it looks like an arbitrary number field.

**Desired behaviour:**  
Currency fields in edit mode display:
- A non-editable currency symbol prefix badge (e.g., "KES") derived from `props.currency` or `doc.currency`
- Right-aligned numeric value
- Thousands separator in the read-only display value; raw number in the focused input (standard financial UX — show 1,234,567 until focused, then 1234567)
- Tabbing away re-applies the formatted display

**Acceptance criteria:**
- All `fieldtype === 'currency'` fields in edit mode show a currency badge prefix
- Badge uses the `currency` prop passed down from the form (not hardcoded KES)
- On blur: value is formatted with commas and 2 decimal places
- On focus: raw number value with no formatting (browser default behaviour)
- Zero values show "0.00" not blank

---

## Epic 2 — Sales Invoice: Item Line Hydration

### FC-05 · Item Rate Auto-Lookup from Price List  `P1`

**Problem today:**  
Selecting `item_code` in a line item row does nothing beyond setting that field. `rate` stays blank. The user must manually look up and type the rate.

**Desired behaviour:**  
When `item_code` changes in a line item row:
1. Fetch `Item Price` from ERPNext: `GET /api/resource/Item Price?filters=[["item_code","=","<code>"],["price_list","=","<selling_price_list>"]]`
2. If found: auto-fill `rate` and `item_name` (and `description` if column exists)
3. If not found: show an inline hint "No price found for this item on Standard Selling" — rate remains editable
4. FC-01 and FC-03 cascade immediately from the new rate

**Acceptance criteria:**
- Rate populates within 500ms of item selection (debounced API call)
- `item_name` column shows the human-readable name alongside `item_code`
- No rate overwrite if the user had previously manually set the rate on that row (dirty flag)
- `selling_price_list` from the invoice header drives the price lookup; changing `selling_price_list` re-fetches all item prices

---

### FC-06 · Item Name + Description Column in Line Items  `P1`

**Problem today:**  
`formLayouts.js` defines only `item_code`, `qty`, `rate` for the items table. Users see internal codes (`CV-HIMS-SUB-ADV`) with no description. For a customer-facing finance view, displaying only codes is ambiguous.

**Desired behaviour:**  
Add two columns to the Sales Invoice line items:
- `item_name` (Data, read-only after FC-05 hydrates it, but manually editable override)
- `description` (Textarea / single-line, optional — collapsed by default, expand on hover)

The `item_name` column appears immediately after `item_code`. It is auto-filled by FC-05 but the user can override the display name per line.

**Acceptance criteria:**
- `item_name` appears as a second column: Item Code | Item Name | Qty | Rate | Amount
- `item_name` auto-fills from FC-05; field is editable (override)
- Column is hidden on mobile (preserves the compact mobile card layout)
- Empty `item_name` shows a subtle placeholder "Item name"

---

## Epic 3 — Payment UX: Mode of Payment

### FC-07 · Mode of Payment — Smart Picker, Not Dropdown  `P0`

**Problem today:**  
`PaymentAllocationForm` renders Mode of Payment as `FormControl type="select"` — a native HTML `<select>`. This is:
- Inconsistent with the `customer` field (which is a Combobox)
- Unusable when there are many modes
- Not searchable
- Not extensible for showing mode icons (card, cash, M-Pesa, bank transfer)
- Reset to empty on every customer change — almost always wrong

**Desired behaviour:**  
Replace the `<select>` with a horizontally-scrollable pill group of the most common payment modes, with a "+ More" overflow that opens a Combobox for additional modes.

Layout:
```
[ Cash ]  [ M-Pesa ]  [ Bank Transfer ]  [ Cheque ]  [ + More ▾ ]
```

Each pill shows:
- An icon (cash, phone, building, document)
- The mode name
- Selected state: filled background using the brand accent token

The "active" mode persists across customer changes unless the user explicitly clears it (UX principle: payment channel is a user habit, not a customer property).

**Acceptance criteria:**
- Top 4 most recently used modes appear as pills (stored in `localStorage` per user, keyed by `fc_recent_modes`)
- Selecting a pill immediately sets `modeOfPayment` and highlights the pill
- "+ More" opens a Combobox searching `Mode of Payment` doctype
- Selected mode from Combobox is added to the pill row and marked active
- Mode of Payment is NOT reset on customer change
- Minimum 2 modes always shown even if no recency data (default: Cash, Bank Transfer)
- If only 1 mode exists on the site, no "+ More" and the single mode is auto-selected

---

### FC-08 · Customer Picker — Smart Search with Context  `P1`

**Problem today:**  
The customer Combobox in `PaymentAllocationForm` searches by `name` (the customer code, e.g. `CUST-00023`) only. Users type customer display names and get no results. There is no disambiguation between customers with similar names.

**Desired behaviour:**  
The customer Combobox searches both `name` AND `customer_name` simultaneously, and renders results with:
- **Primary line:** `customer_name` (bold)
- **Secondary line:** `name` (code, muted) + outstanding balance if available

On selection: show the selected customer's outstanding balance as a context chip:
```
[ Kenyatta National Hospital  ×]   KES 4.2M outstanding
```

**Acceptance criteria:**
- API call uses `or_filters: [["name","like","%q%"],["customer_name","like","%q%"]]`
- Result list shows: customer_name (line 1), customer code + company (line 2)
- After selection, an inline balance chip appears below the picker: "KES X outstanding (N invoices)"
- Balance chip fetches from `crm.finance.api.get_ar_invoices` filtered by customer — 1 API call
- Clearing the customer field clears the balance chip and the invoice table
- Keyboard arrow navigation in the Combobox result list works correctly

---

## Epic 4 — Payment Allocation Form: Full Edit Surface

### FC-09 · Payment Amount Entry + Invoice Suggestion  `P1`

**Problem today:**  
There is no `paid_amount` input field. The user must manually select invoices and enter allocations; the total appears in the footer. This is backwards — a customer typically calls and says "I paid 50,000" and the cashier needs to allocate that against invoices. There is no way to enter the amount first and have the system suggest allocations.

**Desired behaviour:**  
Add a prominent "Amount Received" input above the invoice table:

```
Amount Received:  [ KES  ________________ ]
```

Behaviour when amount is entered:
1. "Auto-Allocate" button appears: clicking it fills the invoice table from oldest-due first until the amount is exhausted
2. If amount < smallest outstanding invoice: warns "Below minimum invoice balance"
3. If amount > total outstanding: shows "Over-payment of KES X — will be left unallocated"
4. The footer shows: Allocated KES X | Unallocated KES Y | Total KES Z

**Acceptance criteria:**
- `paid_amount` input is the first field after the customer picker
- Input is right-aligned, shows currency symbol prefix (FC-04 pattern)
- "Auto-Allocate" button is disabled until both customer and amount are set
- Auto-allocation fills oldest-due invoices first (sort by `due_date asc`)
- Manual override of individual allocations still works after auto-allocate
- Over-payment amount is visible in a yellow callout: "KES X will be posted as unallocated credit"
- The `paid_amount` value is sent to the backend (currently derived from allocations only)

---

### FC-10 · Invoice Table — Sort, Select All, Overdue Highlighting  `P1`

**Problem today:**  
The invoice table has no column sorting, no "select all" checkbox, and shows an "overdue" badge but no visual priority ordering. Users with 10+ invoices cannot quickly see which to pay first.

**Desired behaviour:**  

**Sort controls** (single-column sort, click header to toggle asc/desc):
- Due Date (default: oldest first)
- Outstanding Amount
- Invoice name

**Select all / none:**  
Checkbox in the table header row. When clicked: fills all `_allocated` values to their `outstanding_amount` (or sets all to 0 if all are already selected).

**Overdue visual treatment:**
- Rows with `due_date < today`: red left border (3px), `bg-red-50/30 dark:bg-red-900/10`
- Due within 7 days: amber left border
- Not yet due: no accent

**Acceptance criteria:**
- Column headers Due Date, Outstanding, Invoice Name are clickable sort triggers
- Active sort column shows a ▲/▼ chevron
- Default sort: due_date ascending (oldest due first)
- Select All header checkbox checks all visible rows at their full outstanding amount
- Row overdue accent is derived from `due_date` vs `today` client-side — no extra API call
- Overdue accent is visible without selecting the row (independent of the checkbox state)

---

### FC-11 · Payment Review Step Before Submit  `P1`

**Problem today:**  
Clicking "Record Payment" immediately calls `create_customer_payment` with `submit: 1` — the payment entry posts to the GL instantly with no confirmation. There is no way to review the entry before it is irreversible.

**Desired behaviour:**  
A two-step flow:

**Step 1 — Allocation form** (current form, improved by FC-07/08/09/10)

**Step 2 — Review panel** — slides in before submit:
```
┌─────────────────────────────────────┐
│  Payment Review                      │
│                                      │
│  Customer:   Kenyatta National Hosp  │
│  Amount:     KES 2,200,000           │
│  Mode:       Bank Transfer           │
│  Reference:  TIB-20260810-001        │
│  Date:       10 Aug 2026             │
│                                      │
│  Allocations (2 invoices):           │
│  ACC-SINV-2026-00014  KES 1,500,000  │
│  ACC-SINV-2026-00013  KES 700,000    │
│                                      │
│  Unallocated:  KES 0                 │
│                                      │
│  [← Back to Edit]  [Confirm & Post]  │
└─────────────────────────────────────┘
```

**Acceptance criteria:**
- "Record Payment" button replaced by "Review →"
- Review panel slides in as an in-place transition (same page, no modal)
- All values are read-only in the review step
- "← Back to Edit" returns to the allocation form with all state preserved
- "Confirm & Post" calls the backend and submits
- If backend returns an error, the error is shown in the review panel (not a toast that auto-dismisses)
- Successful post shows a green success state with the Payment Entry name: "PE-2026-00001 posted" + "View in Accounts" link

---

### FC-12 · Reference Number and Date — Contextual Labels  `P2`

**Problem today:**  
`referenceNo` label is "Reference No" and `referenceDate` is "Reference Date" with no guidance about what these fields mean.

**Desired behaviour:**  
The label changes based on the selected Mode of Payment:
- Bank Transfer → "Bank Reference / RTGS Ref" + "Value Date"
- M-Pesa → "M-Pesa Transaction ID" + "Transaction Date"
- Cheque → "Cheque Number" + "Cheque Date"
- Cash → both fields hidden (cash has no external reference)

**Acceptance criteria:**
- Label text is derived from `modeOfPayment` via a static map
- Cash mode: Reference No and Reference Date fields are hidden entirely (and not required)
- Non-cash mode: Reference No is required (marked with *)
- Mode change triggers label update without any flicker

---

## Epic 5 — Sales Invoice Detail View

### FC-13 · Detail Summary Strip — Business-Critical Fields  `P1`

**Problem today:**  
The 5-fact summary strip in `FinanceDetail` takes the first 5 scalar fields — which happens to be `customer`, `company`, `currency`, `selling_price_list`, `posting_date`. The most important financial fields (`due_date`, `outstanding_amount`, `status`) are buried in the Details accordion.

**Desired behaviour:**  
The summary strip for Sales Invoice shows exactly these 5 facts, in this order:
1. Customer
2. Grand Total (KES value, prominent)
3. Status (with colour badge)
4. Due Date (with "X days overdue" if past)
5. Outstanding Amount

**Acceptance criteria:**
- The strip is defined explicitly in `formLayouts.js` for Sales Invoice — not derived positionally
- "X days overdue" appears in red below the Due Date if `due_date < today` and `docstatus === 1`
- Outstanding Amount shows "Paid in Full" in green when `outstanding_amount === 0`
- Grand Total in the strip uses `formatCurrency` — same formatter as the SummaryBar

---

### FC-14 · Related Document Links on Detail View  `P1`

**Problem today:**  
A Sales Invoice detail shows no links to related documents. Users cannot navigate from an invoice to its Payment Entries or back to the CRM Deal without manually searching.

**Desired behaviour:**  
A "Related" panel at the bottom of the detail view showing:

For Sales Invoice:
- CRM Deal link (if `crm_deal` is set) — "View Deal →"
- CRM Quotation link (if `crm_quotation` is set) — "View Quote →"
- Payment Entries (fetched from `payment_entry.references` or `crm.finance.api.get_payment_entries_for_invoice`) — shown as pill links

For Payment Entry:
- Linked invoices from `references` child table — each shown as a link chip

**Acceptance criteria:**
- "Related" section is always rendered but shows "No related documents" when empty
- Each link opens the document in a new tab (Finance Cockpit detail view or CRM tab)
- `crm_deal` link navigates to `/crm/deals/:dealId`
- Payment Entry links use `crm.finance.api.get_customer_payments` filtered by invoice name

---

## Epic 6 — Design System Consistency

### FC-15 · SummaryBar Design Token Alignment  `P2`

**Problem today:**  
`SummaryBar.vue` uses raw Tailwind utilities (`text-gray-500`, `border-gray-200`, `bg-gray-800/50`) throughout. Every other Finance Cockpit component uses the design-system tokens (`text-ink-gray-*`, `border-outline-gray-*`, `bg-surface-*`). In dark mode, SummaryBar will render inconsistently.

**Desired behaviour:**  
Replace every raw gray utility in SummaryBar with the equivalent design-system token:

| Raw | Replace with |
|---|---|
| `text-gray-500` | `text-ink-gray-5` |
| `text-gray-700` | `text-ink-gray-7` |
| `text-gray-900` | `text-ink-gray-9` |
| `border-gray-200` | `border-outline-gray-2` |
| `bg-gray-50` | `bg-surface-gray-1` |
| `bg-gray-800/50` | `bg-surface-gray-8/50` |

Also: the Grand Total row background should use `bg-surface-blue-6 text-ink-blue-1` (brand accent) not `bg-gray-800/50` (arbitrary dark).

**Acceptance criteria:**
- Zero raw `text-gray-*` / `bg-gray-*` / `border-gray-*` classes remaining in SummaryBar.vue
- Light mode: visually indistinguishable from current
- Dark mode: SummaryBar matches the visual weight of the rest of the Finance Cockpit

---

### FC-16 · Tax Breakdown in SummaryBar  `P2`

**Problem today:**  
The SummaryBar shows a single "Tax" line aggregated from all tax rows. When multiple taxes apply (e.g., VAT 16% + WHT 5%), the user cannot see the individual components.

**Desired behaviour:**  
When the `taxes` array has > 0 rows, expand the Tax line into individual rows:

```
Sub Total Excl. VAT    KES 5,000,000
  VAT 16%              KES   800,000
  Withholding Tax 5%   KES   250,000
─────────────────────────────────────
Grand Total            KES 5,800,000   ← (note: WHT is not additive; this is illustrative)
```

Each tax row shows: description (from `description` field of the tax row) + formatted amount.

**Acceptance criteria:**
- Tax breakdown only shows when there is ≥ 1 tax row with `tax_amount > 0`
- Zero-amount tax rows are hidden
- Single tax row: collapsed as before ("Tax  KES X") with no sub-label
- Multiple rows: expanded list, each indented, in the same visual weight
- Grand Total line always stays at the bottom

---

## Playwright Test Stories

### FC-T01 · Sales Invoice — Tax Auto-Calculation  `P0`

Full UI click-path test covering FC-01 and FC-03:

1. Navigate to FC → Invoices → New
2. Select customer
3. Add 1 line item (item_code, qty=1, rate=1,000,000)
4. Verify footer Grand Total = 1,000,000 (no tax yet)
5. Navigate to Taxes section → Apply Tax Template (or add row manually)
6. Enter rate = 16 in the Rate column
7. Assert: `tax_amount` auto-fills to 160,000 (1,000,000 × 0.16)
8. Assert: footer Grand Total = 1,160,000
9. Change item rate to 2,000,000
10. Assert: tax_amount auto-updates to 320,000
11. Assert: footer Grand Total = 2,320,000

### FC-T02 · Payment Flow — Full Click Path  `P1`

1. Navigate to FC → Invoices → find a submitted SI with `outstanding_amount > 0`
2. Click "Receive Payment"
3. Verify: customer pre-filled from the SI customer
4. Enter Amount Received = outstanding_amount
5. Click "Auto-Allocate"
6. Verify: invoice row is checked, allocation = outstanding_amount, Unallocated = 0
7. Select Mode of Payment = Bank Transfer (via pill)
8. Enter Reference No
9. Click "Review →"
10. Verify Review panel shows correct: customer, amount, mode, allocation
11. Click "Confirm & Post"
12. Verify: success state shows Payment Entry name
13. Navigate back to the invoice
14. Verify: `outstanding_amount = 0`, status = "Paid"

### FC-T03 · Mode of Payment Pill Persistence  `P2`

1. Open Payment form, select "M-Pesa" mode
2. Change customer to a different customer
3. Assert: mode is still "M-Pesa" (not reset)
4. Reload the page and re-open the payment form
5. Assert: "M-Pesa" pill is highlighted (persisted in localStorage)

---

## Implementation Sequence

| Story | Effort | Dependency |
|---|---|---|
| FC-01 Tax rate → amount | S | None |
| FC-03 Grand Total live | S | FC-01 |
| FC-04 Currency inputs | S | None |
| FC-07 Mode of Payment pill | M | None |
| FC-08 Customer smart search | S | None |
| FC-09 Amount entry + auto-allocate | M | FC-07 |
| FC-10 Invoice table sort + select all | S | None |
| FC-05 Item rate lookup | M | None |
| FC-06 Item name column | S | FC-05 |
| FC-11 Payment review step | M | FC-09, FC-10 |
| FC-02 Tax template picker | M | FC-01 |
| FC-13 Detail summary strip | S | None |
| FC-14 Related document links | S | None |
| FC-15 SummaryBar tokens | XS | None |
| FC-16 Tax breakdown | S | FC-01 |
| FC-12 Reference labels | XS | FC-07 |
| FC-T01–T03 Tests | M | All above |

S = 0.5–1 day · M = 1–2 days · XS = < 2 hours
