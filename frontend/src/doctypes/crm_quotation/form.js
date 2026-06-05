export class CRMQuotation {
  // Dipanggil saat form pertama kali dimuat.
  onLoad() {
    // Number diisi otomatis → read-only. (Subject dibiarkan editable;
    //  Account read-only di-set di doctype.)
    this.setFieldProperty('number', 'read_only', 1)
  }

  // Dipanggil setelah dokumen ter-render — pastikan data turunan ikut muncul
  // walau untuk quotation lama (contact & detail inquiry).
  async onRender() {
    if (this.doc?.account) {
      await this.fillContactFromAccount()
    }
    await this.fillInquiryDetails()
  }

  // Dipanggil otomatis saat field "inquiry" (Link ke CRM Deal) berubah.
  async inquiry() {
    const inquiry = this.value

    // Inquiry dikosongkan → bersihkan field turunan.
    if (!inquiry) {
      this.doc.number = ''
      this.doc.subject = ''
      this.doc.account = ''
      this.doc.account_name = ''
      this.doc.contact_name = ''
      this.setFieldHtml('inquiry_details', '')
      return
    }

    // Ambil organization & subject dari CRM Deal yang dipilih.
    const deal = await this.call('frappe.client.get_value', {
      doctype: 'CRM Deal',
      filters: { name: inquiry },
      fieldname: ['organization', 'organization_name', 'subject'],
    })
    if (!deal) return

    this.doc.number = inquiry
    this.doc.subject = deal.subject || ''
    this.doc.account = deal.organization || ''
    this.doc.account_name = deal.organization_name || ''

    // Contact mengikuti organization (account) + detail inquiry di sidebar.
    await this.fillContactFromAccount()
    await this.fillInquiryDetails()
  }

  // Dipanggil otomatis saat field "account" berubah (manual maupun dari inquiry).
  async account() {
    await this.fillContactFromAccount()
  }

  // Helper: isi contact_name dari contact milik account/organization.
  async fillContactFromAccount() {
    const account = this.doc.account
    if (!account) {
      this.doc.contact_name = ''
      return
    }

    const contacts = await this.call('frappe.client.get_list', {
      doctype: 'Contact',
      filters: { company_name: account },
      fields: ['name'],
      order_by: 'creation asc',
      limit_page_length: 1,
    })

    const c = contacts && contacts[0]
    this.doc.contact_name = c ? c.name : ''
  }

  // Helper: render detail CRM Deal (inquiry) ke HTML field di sidebar.
  async fillInquiryDetails() {
    const inquiry = this.doc.inquiry
    console.log('[CRMQuotation] fillInquiryDetails, inquiry =', inquiry)
    if (!inquiry) {
      this.setFieldHtml('inquiry_details', '')
      return
    }

    const d = await this.call('crm.api.quotation.get_inquiry_detail', {
      name: inquiry,
    })
    console.log('[CRMQuotation] get_inquiry_detail =', d)

    if (!d || !d.name) {
      this.setFieldHtml('inquiry_details', '')
      return
    }

    const esc = (v) =>
      String(v).replace(/[&<>"]/g, (s) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
      })[s])

    const row = (label, val) =>
      val
        ? `<div style="display:flex;justify-content:space-between;gap:8px;padding:3px 0;font-size:13px">
             <span style="color:var(--text-ink-gray-5,#6b7280);flex-shrink:0">${label}</span>
             <span style="color:var(--text-ink-gray-8,#1f272e);text-align:right;word-break:break-word">${esc(val)}</span>
           </div>`
        : ''

    const html = `
      <div>
        ${row('Inquiry', d.name)}
        ${row('Organization', d.organization)}
        ${row('Subject', d.subject)}
        ${row('Status', d.status)}
        ${row('Contact', d.contact_name)}
        ${row('Email', d.email)}
        ${row('Mobile', d.mobile_no)}
        ${row('Territory', d.territory)}
        ${row('Source', d.source)}
        ${row('Owner', d.deal_owner)}
      </div>`

    this.setFieldHtml('inquiry_details', html)
    console.log('[CRMQuotation] setFieldHtml inquiry_details panjang =', html.length)
  }
}
