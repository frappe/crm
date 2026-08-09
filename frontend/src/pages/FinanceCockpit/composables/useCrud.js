import { ref } from 'vue'
import { createResource } from 'frappe-ui'

/**
 * Native Frappe CRUD factory for the Finance Cockpit.
 *
 * NO custom backend facade. Every operation hits Frappe's native, permission-
 * enforced client endpoints via frappe-ui createResource:
 *
 *   load   -> frappe.client.get      (doctype, name)
 *   insert -> frappe.client.insert   (doc: full JSON incl. doctype + child arrays)
 *   update -> frappe.client.save     (doc: full JSON incl. doctype + name)
 *   submit -> frappe.client.submit   (doc: full JSON)
 *   cancel -> frappe.client.cancel   (doctype, name)
 *   delete -> frappe.client.delete   (doctype, name)
 *
 * Field metadata is NOT fetched from the server — the curated shape lives in
 * constants/formLayouts.js (resolveLayout). Child tables travel as nested
 * arrays inside the same doc object, exactly as Frappe expects.
 *
 * frappe-ui unwraps the RPC envelope, so `resource.submit()` resolves to the
 * returned doc dict directly. Every throw is normalized to a readable string.
 */

export function readableError(err) {
  if (!err) return ''
  if (Array.isArray(err.messages) && err.messages.length) return err.messages.join('\n')
  if (typeof err === 'string') return err
  return err.message || 'Something went wrong. Please try again.'
}

export function useCrud(doctype) {
  const loading = ref(false)
  const error = ref('')

  function makeResource(method, httpMethod = 'POST') {
    return createResource({ url: `frappe.client.${method}`, method: httpMethod })
  }

  async function run(resource, params) {
    loading.value = true
    error.value = ''
    try {
      return await resource.submit(params)
    } catch (err) {
      error.value = readableError(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /** Load a full document (child tables included) by name. */
  async function loadDoc(name) {
    return run(makeResource('get', 'GET'), { doctype, name })
  }

  /**
   * Insert (no name) or update (has name). The doc object is sent whole —
   * doctype is injected and child tables ride along as nested arrays.
   */
  async function saveDoc(docObj) {
    const payload = { ...docObj, doctype }
    const isUpdate = !!docObj.name
    const res = makeResource(isUpdate ? 'save' : 'insert', isUpdate ? 'PUT' : 'POST')
    return run(res, { doc: JSON.stringify(payload) })
  }

  /** Submit a document. Accepts the full doc object (post-save). */
  async function submitDoc(docObj) {
    const payload = { ...docObj, doctype }
    return run(makeResource('submit', 'PUT'), { doc: JSON.stringify(payload) })
  }

  async function cancelDoc(name) {
    return run(makeResource('cancel', 'PUT'), { doctype, name })
  }

  async function deleteDoc(name) {
    return run(makeResource('delete', 'DELETE'), { doctype, name })
  }

  return { loadDoc, saveDoc, submitDoc, cancelDoc, deleteDoc, loading, error }
}
