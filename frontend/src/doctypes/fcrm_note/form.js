export class FCRMNote {
  onRender() {
    if (this.doc.reference_doctype && this.doc.reference_docname) {
      let label = this.doc.reference_doctype.replace('CRM ', '')

      if (!this.actions.some((action) => action.name === 'Redirect Action')) {
        this.actions.push({
          name: 'Redirect Action',
          label: __('Open {0}', [label]),
          onClick: () => {
            if (!this.doc.reference_docname) return
            let name =
              this.doc.reference_doctype == 'CRM Deal' ? 'Deal' : 'Lead'
            let params = { leadId: this.doc.reference_docname }
            if (name == 'Deal') {
              params = { dealId: this.doc.reference_docname }
            }
            this.router.push({ name: name, params: params })
          },
        })
      }
    }
  }
}
