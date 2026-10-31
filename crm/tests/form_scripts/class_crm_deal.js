// A class-based CRM Form Script on CRM Deal, with a CRM Products child class (frappe/frappe#45966).
// A `hits:` comment lists the catalog keys the analysis finds on its line.
class CRMDeal {
  onLoad() { // hits: on-load
    if (this.doc.__newDocument) return // hits: new-document
    this.actions = [ // hits: header-actions
      {
        label: __('Refresh probability'), // hits: translate
        onClick: () => this.doc.trigger('updateProbability'), // hits: action-on-click, doc-trigger
      },
      {
        group: __('More'), // hits: action-group, translate
        hideLabel: true,
        items: [
          { label: __('Show next step'), onClick: () => this.showNextStep() }, // hits: translate, action-on-click, this-method-call
          { label: __('Edit next step'), onClick: () => this.editNextStep() }, // hits: translate, action-on-click, this-method-call
          { label: __('Open settings'), onClick: () => crm.openSettings('General') }, // hits: translate, action-on-click, open-settings
          { label: __('All leads'), onClick: () => router.push({ name: 'Leads' }) }, // hits: translate, action-on-click, router
        ],
      },
    ]
    // `h` and `this.tabs` exist on CRM develop only
    if (typeof h === 'function') {
      this.tabs = [ // hits: tabs
        { name: 'summary', label: __('Summary'), component: { render: () => h('p', this.doc.next_step) } }, // hits: translate, h-helper
      ]
    }
  }

  onRender() { // hits: on-render
    this.setFieldProperty('next_step', 'hidden', !this.doc.probability) // hits: set-field-property
    this.setFieldProperty('details_section', 'label', __('Deal details')) // hits: section-property, translate
    this.setFieldProperty('organization_section', 'opened', true) // hits: panel-section-property
    this.setFieldProperty('first_tab', 'label', __('Overview')) // hits: tab-property, translate
    this.setFieldProperty('status', 'button_color', 'green') // hits: field-props
    this.setFieldProperties('probability', { description: __('Set from the status') }) // hits: set-field-properties, translate
    if (this.doc.status === 'Won') {
      this.setFieldHtml('next_step', `<p>${__('Deal won')}</p>`) // hits: set-field-html, translate
    }
  }

  onValidate() { // hits: on-validate
    const probability = this.getField('probability') // hits: get-field
    if (probability.reqd && !this.doc.probability) {
      throwError(__('Set a probability')) // hits: throw-error, translate
    }
  }

  onSave() { // hits: on-save
    this.removeFieldProperty('next_step', 'hidden') // hits: remove-field-property
    this.toast.success(__('Deal saved')) // hits: toast-success, translate
  }

  status() { // hits: field-handler
    this.doc.trigger('updateProbability') // hits: doc-trigger
  }

  probability() { // hits: field-handler
    if (this.value > 100) toast.error(__('Probability cannot be above 100')) // hits: this-value, toast-error, translate
  }

  async updateProbability() {
    const status = await call('frappe.client.get_value', { // hits: call
      doctype: 'CRM Deal Status',
      fieldname: 'probability',
      filters: { name: this.doc.status },
    })
    this.doc.probability = status.probability
  }

  updateTotal() {
    this.doc.total = this.doc.products.reduce((total, row) => total + (row.amount || 0), 0)
    this.doc.net_total = this.doc.total
  }

  showNextStep() {
    createDialog({ // hits: create-dialog
      title: __('Next step'), // hits: translate
      html: `<p>${this.doc.next_step || __('No next step yet')}</p>`, // hits: create-dialog-html, translate
      actions: [{ label: __('Close'), variant: 'solid', onClick: ({ close }) => close() }], // hits: translate
    })
  }

  async editNextStep() {
    const meta = await this.getMeta('CRM Deal') // hits: get-meta
    const label = meta.fields.find((field) => field.fieldname === 'next_step').label
    const values = await formDialog({ // hits: form-dialog
      title: __('Edit next step'), // hits: translate
      fields: [{ fieldname: 'next_step', fieldtype: 'Data', label }],
      defaults: { next_step: this.doc.next_step },
    })
    if (values) this.doc.next_step = values.next_step
  }
}

class CRMProducts { // hits: child-class
  products_add() { // hits: row-add
    const row = this.getRow('products', this.currentRowIdx) // hits: get-row, current-row-idx
    row.qty = row.qty || 1
    row.trigger('qty') // hits: row-trigger
  }

  products_remove() { // hits: row-remove
    toast.success(__('{0} products left', [this.rows.length])) // hits: toast-success, translate, remaining-rows
    this.doc.trigger('updateTotal') // hits: doc-trigger
  }

  qty() { // hits: child-field-handler
    const row = this.doc.getRow('products') // hits: get-row
    row.amount = row.qty * row.rate
    this.doc.trigger('updateTotal') // hits: doc-trigger
  }
}
