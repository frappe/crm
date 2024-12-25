import { createResource } from 'frappe-ui'
import { formatCurrency } from '@/utils/numberFormat.js'
import { reactive } from 'vue'

const doctypeMeta = reactive({})

export function getMeta(doctype) {
  const meta = createResource({
    url: 'frappe.desk.form.load.getdoctype',
    params: {
      doctype: doctype,
      with_parent: 1,
      cached_timestamp: null,
    },
    cache: ['Meta', doctype],
    onSuccess: (res) => {
      let dtMetas = res.docs
      for (let dtMeta of dtMetas) {
        doctypeMeta[dtMeta.name] = dtMeta
      }
    },
  })

  if (!doctypeMeta[doctype]) {
    meta.fetch()
  }

  function getFormattedCurrency(fieldname, doc) {
    let currency = window.sysdefaults.currency || 'USD'

    let df = doctypeMeta[doctype]?.fields.find((f) => f.fieldname == fieldname)

    if (df && df.options) {
      if (df.options.indexOf(':') != -1) {
        currency = currency
      } else if (doc && doc[df.options]) {
        currency = doc[df.options]
      }
    }

    return formatCurrency(doc[fieldname], df, currency)
  }

  return {
    meta,
    doctypeMeta,
    getFormattedCurrency,
  }
}
