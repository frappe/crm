/**
 * FRONTEND field-curation config for the Finance Cockpit CRUD engine.
 *
 * There is NO backend get_form_meta anymore. This file is the SOLE source of
 * truth for which fields a doctype exposes in the cockpit, their types, labels,
 * options, and required flags. The CRUD components read from here directly and
 * talk to Frappe's native client endpoints (frappe.client.*) for persistence.
 *
 * Field shape (normalized — used by FieldRenderer & LineItemsGrid):
 *   {
 *     fieldname,             // doc key
 *     label,                 // display label
 *     type,                  // 'link'|'date'|'datetime'|'currency'|'float'|'int'
 *                            //   |'check'|'select'|'textarea'|'data'
 *     options,               // link: target doctype (string); select: string[]
 *     optionsField,          // link: sibling fieldname holding the target doctype
 *                            //   (Dynamic Link — overrides `options` at render time)
 *     required,              // boolean
 *     readOnly,              // boolean (optional)
 *     precision,             // number of decimals for numeric fields (optional)
 *     default,               // seed value for new docs (optional) — used for
 *                            //   workflow-driven readOnly fields like `status`
 *   }
 *
 * Section shape:
 *   {
 *     key, title, icon,      // header + Lucide icon name (see FcIcon)
 *     kind,                  // 'fields' | 'lineItems' | 'taxes' | 'summary'
 *     fields: [fieldObj...], // for kind:'fields'
 *     columns: [fieldObj...],// for kind:'lineItems' | 'taxes'
 *     tableField,            // child table key for lineItems / taxes
 *     collapsible, collapsed,// taxes region
 *     hero,                  // lineItems visual emphasis
 *     qtyField, rateField, amountField,  // lineItems live-calc mapping
 *   }
 */

const CHARGE_TYPES = [
  'Actual',
  'On Net Total',
  'On Previous Row Amount',
  'On Previous Row Total',
  'On Item Quantity',
]

export const FORM_LAYOUTS = {
  'Sales Invoice': {
    isSubmittable: true,
    statusField: 'status',
    remarksField: 'remarks',
    // Live-calc + summary mapping for the invoice composer.
    totals: {
      lineItemsField: 'items',
      qtyField: 'qty',
      rateField: 'rate',
      amountField: 'amount',
      subtotalField: 'total',
      taxRowsField: 'taxes',
      taxAmountField: 'tax_amount',
      taxTotalField: 'total_taxes_and_charges',
      grandTotalField: 'grand_total',
    },
    sections: [
      {
        key: 'parties',
        title: 'Customer & Billing',
        icon: 'user',
        kind: 'fields',
        fields: [
          { fieldname: 'customer', label: 'Customer', type: 'link', options: 'Customer', required: true },
          { fieldname: 'company', label: 'Company', type: 'link', options: 'Company', required: true },
          { fieldname: 'currency', label: 'Currency', type: 'link', options: 'Currency' },
          { fieldname: 'selling_price_list', label: 'Price List', type: 'link', options: 'Price List' },
        ],
      },
      {
        key: 'schedule',
        title: 'Dates',
        icon: 'calendar',
        kind: 'fields',
        fields: [
          { fieldname: 'posting_date', label: 'Posting Date', type: 'date', required: true },
          { fieldname: 'due_date', label: 'Due Date', type: 'date' },
        ],
      },
      {
        key: 'items',
        title: 'Line Items',
        icon: 'list',
        kind: 'lineItems',
        tableField: 'items',
        qtyField: 'qty',
        rateField: 'rate',
        amountField: 'amount',
        hero: true,
        columns: [
          { fieldname: 'item_code', label: 'Item', type: 'link', options: 'Item', required: true },
          { fieldname: 'item_name', label: 'Description', type: 'data', wideOnly: true },
          { fieldname: 'qty', label: 'Qty', type: 'float', required: true },
          { fieldname: 'rate', label: 'Rate', type: 'currency', required: true },
        ],
      },
      {
        key: 'taxes',
        title: 'Taxes & Charges',
        icon: 'percent',
        kind: 'taxes',
        tableField: 'taxes',
        collapsible: true,
        collapsed: true,
        columns: [
          { fieldname: 'charge_type', label: 'Type', type: 'select', options: CHARGE_TYPES, required: true },
          { fieldname: 'account_head', label: 'Account', type: 'link', options: 'Account', required: true },
          { fieldname: 'description', label: 'Description', type: 'data', required: true, wideOnly: true },
          { fieldname: 'rate', label: 'Rate %', type: 'float' },
          { fieldname: 'tax_amount', label: 'Amount', type: 'currency' },
        ],
      },
      {
        key: 'options',
        title: 'Options',
        icon: 'settings-2',
        kind: 'fields',
        fields: [
          { fieldname: 'update_stock', label: 'Update Stock', type: 'check' },
          { fieldname: 'cost_center', label: 'Cost Center', type: 'link', options: 'Cost Center' },
        ],
      },
      {
        key: 'summary',
        title: 'Summary',
        icon: 'coins',
        kind: 'summary',
        remarksField: 'remarks',
        remarksLabel: 'Remarks',
      },
    ],
    summaryFields: ['customer', 'grand_total', 'status', 'due_date', 'outstanding_amount'],
  },

  Quotation: {
    isSubmittable: true,
    statusField: 'status',
    remarksField: 'tc_name',
    remarksLabel: 'Terms',
    totals: {
      lineItemsField: 'items',
      qtyField: 'qty',
      rateField: 'rate',
      amountField: 'amount',
      subtotalField: 'total',
      taxRowsField: 'taxes',
      taxAmountField: 'tax_amount',
      taxTotalField: 'total_taxes_and_charges',
      grandTotalField: 'grand_total',
    },
    sections: [
      {
        key: 'parties',
        title: 'Customer & Company',
        icon: 'user',
        kind: 'fields',
        fields: [
          // party_name is a Dynamic Link whose target doctype is set by the sibling
          // quotation_to field. `optionsField` tells FieldRenderer to resolve the link
          // target reactively from doc.quotation_to (Customer / Lead / Prospect).
          // Changing quotation_to clears party_name (see FinanceForm.setField).
          { fieldname: 'quotation_to', label: 'Quotation To', type: 'select', options: ['Customer', 'Lead', 'Prospect'], required: true, default: 'Customer' },
          { fieldname: 'party_name', label: 'Party', type: 'link', optionsField: 'quotation_to', required: true },
          { fieldname: 'company', label: 'Company', type: 'link', options: 'Company', required: true },
          { fieldname: 'order_type', label: 'Order Type', type: 'select', options: ['Sales', 'Maintenance', 'Shopping Cart'], required: true },
          { fieldname: 'currency', label: 'Currency', type: 'link', options: 'Currency' },
          { fieldname: 'selling_price_list', label: 'Price List', type: 'link', options: 'Price List' },
        ],
      },
      {
        key: 'schedule',
        title: 'Dates',
        icon: 'calendar',
        kind: 'fields',
        fields: [
          { fieldname: 'transaction_date', label: 'Date', type: 'date', required: true },
          { fieldname: 'valid_till', label: 'Valid Till', type: 'date' },
        ],
      },
      {
        key: 'items',
        title: 'Line Items',
        icon: 'list',
        kind: 'lineItems',
        tableField: 'items',
        qtyField: 'qty',
        rateField: 'rate',
        amountField: 'amount',
        hero: true,
        columns: [
          { fieldname: 'item_code', label: 'Item', type: 'link', options: 'Item', required: true },
          { fieldname: 'item_name', label: 'Description', type: 'data', wideOnly: true },
          { fieldname: 'qty', label: 'Qty', type: 'float', required: true },
          { fieldname: 'rate', label: 'Rate', type: 'currency', required: true },
        ],
      },
      {
        key: 'taxes',
        title: 'Taxes & Charges',
        icon: 'percent',
        kind: 'taxes',
        tableField: 'taxes',
        collapsible: true,
        collapsed: true,
        columns: [
          { fieldname: 'charge_type', label: 'Type', type: 'select', options: CHARGE_TYPES, required: true },
          { fieldname: 'account_head', label: 'Account', type: 'link', options: 'Account', required: true },
          { fieldname: 'description', label: 'Description', type: 'data', required: true, wideOnly: true },
          { fieldname: 'rate', label: 'Rate %', type: 'float' },
          { fieldname: 'tax_amount', label: 'Amount', type: 'currency' },
        ],
      },
      {
        key: 'summary',
        title: 'Summary',
        icon: 'coins',
        kind: 'summary',
        remarksField: 'terms',
        remarksLabel: 'Terms & Conditions',
      },
    ],
    summaryFields: ['party_name', 'grand_total', 'status', 'transaction_date', 'valid_till'],
  },

  'Sales Order': {
    isSubmittable: true,
    statusField: 'status',
    remarksField: 'terms',
    remarksLabel: 'Terms & Conditions',
    totals: {
      lineItemsField: 'items',
      qtyField: 'qty',
      rateField: 'rate',
      amountField: 'amount',
      subtotalField: 'total',
      taxRowsField: 'taxes',
      taxAmountField: 'tax_amount',
      taxTotalField: 'total_taxes_and_charges',
      grandTotalField: 'grand_total',
    },
    sections: [
      {
        key: 'parties',
        title: 'Customer & Company',
        icon: 'user',
        kind: 'fields',
        fields: [
          { fieldname: 'customer', label: 'Customer', type: 'link', options: 'Customer', required: true },
          { fieldname: 'company', label: 'Company', type: 'link', options: 'Company', required: true },
          { fieldname: 'order_type', label: 'Order Type', type: 'select', options: ['Sales', 'Maintenance', 'Shopping Cart'], required: true },
          { fieldname: 'currency', label: 'Currency', type: 'link', options: 'Currency' },
          { fieldname: 'selling_price_list', label: 'Price List', type: 'link', options: 'Price List' },
        ],
      },
      {
        key: 'schedule',
        title: 'Dates',
        icon: 'calendar',
        kind: 'fields',
        fields: [
          { fieldname: 'transaction_date', label: 'Date', type: 'date', required: true },
          { fieldname: 'delivery_date', label: 'Delivery Date', type: 'date' },
        ],
      },
      {
        key: 'items',
        title: 'Line Items',
        icon: 'list',
        kind: 'lineItems',
        tableField: 'items',
        qtyField: 'qty',
        rateField: 'rate',
        amountField: 'amount',
        hero: true,
        columns: [
          { fieldname: 'item_code', label: 'Item', type: 'link', options: 'Item', required: true },
          { fieldname: 'item_name', label: 'Description', type: 'data', wideOnly: true },
          { fieldname: 'qty', label: 'Qty', type: 'float', required: true },
          { fieldname: 'rate', label: 'Rate', type: 'currency', required: true },
          { fieldname: 'delivery_date', label: 'Delivery', type: 'date' },
        ],
      },
      {
        key: 'taxes',
        title: 'Taxes & Charges',
        icon: 'percent',
        kind: 'taxes',
        tableField: 'taxes',
        collapsible: true,
        collapsed: true,
        columns: [
          { fieldname: 'charge_type', label: 'Type', type: 'select', options: CHARGE_TYPES, required: true },
          { fieldname: 'account_head', label: 'Account', type: 'link', options: 'Account', required: true },
          { fieldname: 'description', label: 'Description', type: 'data', required: true, wideOnly: true },
          { fieldname: 'rate', label: 'Rate %', type: 'float' },
          { fieldname: 'tax_amount', label: 'Amount', type: 'currency' },
        ],
      },
      {
        key: 'summary',
        title: 'Summary',
        icon: 'coins',
        kind: 'summary',
        remarksField: 'terms',
        remarksLabel: 'Terms & Conditions',
      },
    ],
    summaryFields: ['customer', 'grand_total', 'status', 'transaction_date', 'delivery_date'],
  },

  // Read/detail-only layout: creation goes through PaymentAllocationForm, and
  // submitted payments are not editable — this drives FinanceDetail rendering.
  'Payment Entry': {
    isSubmittable: true,
    statusField: 'status',
    remarksField: 'remarks',
    remarksLabel: 'Remarks',
    totals: null,
    sections: [
      {
        key: 'main',
        title: 'Payment Details',
        icon: 'banknote',
        kind: 'fields',
        fields: [
          { fieldname: 'party', label: 'Customer', type: 'link', options: 'Customer', readOnly: true },
          { fieldname: 'company', label: 'Company', type: 'link', options: 'Company', readOnly: true },
          { fieldname: 'posting_date', label: 'Posting Date', type: 'date', readOnly: true },
          { fieldname: 'mode_of_payment', label: 'Mode', type: 'link', options: 'Mode of Payment', readOnly: true },
          { fieldname: 'paid_amount', label: 'Paid Amount', type: 'currency', readOnly: true },
          { fieldname: 'unallocated_amount', label: 'Unallocated', type: 'currency', readOnly: true },
          { fieldname: 'reference_no', label: 'Reference No.', type: 'data', readOnly: true },
          { fieldname: 'reference_date', label: 'Reference Date', type: 'date', readOnly: true },
        ],
      },
    ],
  },

  'CRM Partner Rebate Voucher': {
    isSubmittable: false,
    statusField: 'status',
    remarksField: null,
    remarksLabel: 'Notes',
    totals: null,
    sections: [
      {
        key: 'main',
        title: 'Rebate Details',
        icon: 'handshake',
        kind: 'fields',
        fields: [
          { fieldname: 'partner', label: 'Partner', type: 'link', options: 'CRM Partner', required: true },
          { fieldname: 'deal', label: 'Deal', type: 'link', options: 'CRM Deal', required: true },
          { fieldname: 'customer', label: 'Customer', type: 'link', options: 'Customer', required: true },
          { fieldname: 'payment_reference', label: 'Payment Reference', type: 'link', options: 'Payment Entry', required: true },
          { fieldname: 'rebate_structure', label: 'Rebate Structure', type: 'link', options: 'CRM Rebate Structure' },
          { fieldname: 'rebate_amount', label: 'Rebate Amount', type: 'currency', required: true },
          { fieldname: 'currency', label: 'Currency', type: 'link', options: 'Currency' },
          // status is workflow-driven (approve/reject/mark-paid endpoints, Finance-Manager
          // gated). Never user-editable here — seeded to the DocType default ('Pending') and
          // surfaced read-only via StatusBadge in the list + detail header.
          { fieldname: 'status', label: 'Status', type: 'select', options: ['Pending', 'Approved', 'Rejected', 'Paid'], readOnly: true, default: 'Pending' },
          { fieldname: 'rejection_reason', label: 'Rejection Reason', type: 'textarea', readOnly: true },
        ],
      },
    ],
  },

  'CRM Sales Commission': {
    isSubmittable: false,
    statusField: 'status',
    remarksField: null,
    remarksLabel: 'Notes',
    totals: null,
    sections: [
      {
        key: 'main',
        title: 'Commission Details',
        icon: 'handshake',
        kind: 'fields',
        fields: [
          { fieldname: 'sales_person', label: 'Sales Person', type: 'link', options: 'User', required: true },
          { fieldname: 'deal', label: 'Deal', type: 'link', options: 'CRM Deal', required: true },
          { fieldname: 'customer', label: 'Customer', type: 'link', options: 'Customer', required: true },
          { fieldname: 'payment_reference', label: 'Payment Reference', type: 'link', options: 'Payment Entry', required: true },
          { fieldname: 'commission_pct', label: 'Commission %', type: 'float', required: true },
          { fieldname: 'commission_amount', label: 'Commission Amount', type: 'currency', required: true },
          { fieldname: 'currency', label: 'Currency', type: 'link', options: 'Currency' },
          // status is workflow-driven (confirm/reject/mark-paid endpoints, Finance-Manager
          // gated). Never user-editable here — seeded to the DocType default ('Reported') and
          // surfaced read-only via StatusBadge in the list + detail header.
          { fieldname: 'status', label: 'Status', type: 'select', options: ['Reported', 'Confirmed', 'Rejected', 'Paid'], readOnly: true, default: 'Reported' },
        ],
      },
    ],
  },
}

const NUMERIC_TYPES = new Set(['int', 'float', 'currency'])

/**
 * Resolve the curated layout for a doctype.
 * Returns a fully-normalized structure the CRUD components consume directly —
 * no backend meta involved.
 *
 * {
 *   hasLayout, isSubmittable, statusField, remarksField, remarksLabel, totals,
 *   sections: [...],                     // each fields-section carries field objects,
 *                                        //   each child section carries `columns`
 *   scalarFields: [fieldObj...],         // every editable scalar (for seed/save)
 *   scalarByName: { fieldname: fieldObj },
 *   childTables: [{ tableField, columns }...],
 * }
 */
export function resolveLayout(doctype) {
  const config = FORM_LAYOUTS[doctype]

  if (!config) {
    return {
      hasLayout: false,
      isSubmittable: false,
      statusField: 'status',
      remarksField: null,
      remarksLabel: 'Notes',
      totals: null,
      sections: [],
      scalarFields: [],
      scalarByName: {},
      childTables: [],
    }
  }

  const scalarFields = []
  const scalarByName = {}
  const childTables = []
  const sections = config.sections.map((sec) => {
    if (sec.kind === 'fields') {
      const fields = (sec.fields || []).map(normalizeField)
      fields.forEach((f) => {
        scalarFields.push(f)
        scalarByName[f.fieldname] = f
      })
      return { ...sec, fields }
    }
    if (sec.kind === 'lineItems' || sec.kind === 'taxes') {
      const columns = (sec.columns || []).map(normalizeField)
      childTables.push({ tableField: sec.tableField, columns })
      return { ...sec, columns }
    }
    return { ...sec }
  })

  // remarks is a scalar we must seed/save even though it renders in SummaryBar.
  if (config.remarksField && !scalarByName[config.remarksField]) {
    const remarksField = normalizeField({
      fieldname: config.remarksField,
      label: config.remarksLabel || 'Notes',
      type: 'textarea',
    })
    scalarFields.push(remarksField)
    scalarByName[remarksField.fieldname] = remarksField
  }

  return {
    hasLayout: true,
    isSubmittable: !!config.isSubmittable,
    statusField: config.statusField || 'status',
    remarksField: config.remarksField || null,
    remarksLabel: config.remarksLabel || 'Notes',
    totals: config.totals || null,
    sections,
    scalarFields,
    scalarByName,
    childTables,
    summaryFields: config.summaryFields || null,
  }
}

function normalizeField(f) {
  return {
    fieldname: f.fieldname,
    label: f.label || f.fieldname,
    type: f.type || 'data',
    options: f.options ?? null,
    // For Dynamic Link fields: name of the sibling field whose value is the
    // target doctype. When set, the effective link target is resolved at render
    // time from doc[optionsField] instead of the static `options` string.
    optionsField: f.optionsField ?? null,
    required: !!f.required,
    readOnly: !!f.readOnly,
    precision: f.precision ?? null,
    default: f.default ?? null,
    wideOnly: !!f.wideOnly,
  }
}

export function isNumericType(type) {
  return NUMERIC_TYPES.has(type)
}
