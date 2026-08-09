import { ref } from 'vue'
import { createResource } from 'frappe-ui'
import { readableError } from './useCrud.js'

/**
 * "Create From" (mapped-doc) helper for the Finance Cockpit.
 *
 * ERPNext exposes whitelisted mappers that turn a SUBMITTED source document into
 * an UNSAVED target doc dict (header + items + taxes + sales team copied, taxes
 * recalculated). Nothing is persisted — the returned dict is reviewed in the
 * cockpit's FinanceForm and saved via the existing frappe.client.insert path.
 *
 * Confirmed mapper endpoints (all @frappe.whitelist(), all validate
 * source.docstatus == 1, signature (source_name, target_doc=None, args=None)):
 *   erpnext.selling.doctype.quotation.quotation.make_sales_order
 *   erpnext.selling.doctype.quotation.quotation.make_sales_invoice
 *   erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice
 *   erpnext.selling.doctype.sales_order.sales_order.make_delivery_note
 *
 * frappe-ui's createResource().submit() unwraps Frappe's { message: ... } RPC
 * envelope, so mapDoc() resolves to the target doc dict directly.
 */
export function useMappedDoc() {
  const loading = ref(false)
  const error = ref('')

  /**
   * Call a whitelisted ERPNext mapper and return the unsaved target doc dict.
   * @param {string} method  Dotted whitelisted path (e.g.
   *   'erpnext.selling.doctype.quotation.quotation.make_sales_order').
   * @param {string} sourceName  Name of the SUBMITTED source document.
   * @returns {Promise<object>} The mapped (unsaved) target doc dict.
   */
  async function mapDoc(method, sourceName) {
    loading.value = true
    error.value = ''
    try {
      // A fresh resource per call — the mapper method varies by flow and each
      // request is one-shot. source_name is the mapper's first positional arg.
      const resource = createResource({ url: method, method: 'POST' })
      const doc = await resource.submit({ source_name: sourceName })
      return doc
    } catch (err) {
      error.value = readableError(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  return { mapDoc, loading, error }
}
