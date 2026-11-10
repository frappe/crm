import { toColumnToFieldMap } from '@/utils/setup'
import { globalStore } from '@/stores/global'
import { call } from 'frappe-ui'
import { onBeforeUnmount, ref, shallowRef } from 'vue'

const API = 'frappe.core.doctype.data_import.data_import'
const POLL_INTERVAL = 2000

export function useLeadImport() {
  const { $socket } = globalStore()
  const dataImport = shallowRef(null)
  const preview = shallowRef(null)
  const progress = ref(null)
  let pollTimer = null
  let onBlocked = null

  async function createImport(fileUrl) {
    dataImport.value = await call('frappe.client.insert', {
      doc: {
        doctype: 'Data Import',
        reference_doctype: 'CRM Lead',
        import_type: 'Insert New Records',
        mute_emails: 1,
        import_file: fileUrl,
      },
    })
    await loadPreview()
  }

  async function loadPreview() {
    preview.value = await call(`${API}.get_preview_from_template`, {
      data_import: dataImport.value.name,
      import_file: dataImport.value.import_file,
    })
  }

  async function saveMapping(mappings) {
    await call('frappe.client.set_value', {
      doctype: 'Data Import',
      name: dataImport.value.name,
      fieldname: 'template_options',
      value: JSON.stringify({
        column_to_field_map: toColumnToFieldMap(mappings),
      }),
    })
    await loadPreview()
  }

  function runImport() {
    return new Promise((resolve, reject) => {
      let settled = false
      const finish = (result) => {
        if (settled) return
        settled = true
        stopListening()
        resolve(result)
      }
      listenForProgress(finish)
      call(`${API}.form_start_import`, { data_import: dataImport.value.name })
        .then(() => !settled && pollStatus(finish))
        .catch((error) => {
          settled = true
          stopListening()
          reject(error)
        })
    })
  }

  function listenForProgress(finish) {
    $socket?.on('data_import_progress', onProgress)
    onBlocked = (data) => {
      if (data.data_import !== dataImport.value?.name) return
      getResult().then(finish)
    }
    $socket?.on('data_import_blocked', onBlocked)
  }

  function onProgress(data) {
    if (data.data_import !== dataImport.value?.name) return
    progress.value = { current: data.current, total: data.total }
  }

  function pollStatus(finish) {
    pollTimer = setTimeout(async () => {
      const result = await getResult().catch(() => null)
      if (result && result.status !== 'Pending') finish(result)
      else if (pollTimer) pollStatus(finish)
    }, POLL_INTERVAL)
  }

  async function getResult() {
    const name = dataImport.value.name
    const [doc, logs] = await Promise.all([
      call('frappe.client.get_value', {
        doctype: 'Data Import',
        filters: name,
        fieldname: ['status', 'template_warnings'],
      }),
      call(`${API}.get_import_logs`, { data_import: name }),
    ])
    return {
      status: doc.status,
      warnings: parseWarnings(doc.template_warnings),
      imported: logs.filter((log) => log.success).length,
      failedRows: logs.filter((log) => !log.success),
    }
  }

  function stopListening() {
    clearTimeout(pollTimer)
    pollTimer = null
    $socket?.off('data_import_progress', onProgress)
    if (onBlocked) $socket?.off('data_import_blocked', onBlocked)
  }

  onBeforeUnmount(stopListening)

  return {
    dataImport,
    preview,
    progress,
    createImport,
    saveMapping,
    runImport,
  }
}

function parseWarnings(value) {
  if (!value) return []
  try {
    return JSON.parse(value)
  } catch {
    return []
  }
}
