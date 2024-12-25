import { createResource } from 'frappe-ui'
import { formatCurrency, formatNumber } from '@/utils/numberFormat.js'
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

  function getFormattedPercent(fieldname, doc) {
    let value = getFormattedFloat(fieldname, doc)
    return value + '%'
  }

  function getFormattedFloat(fieldname, doc) {
    let df = doctypeMeta[doctype]?.fields.find((f) => f.fieldname == fieldname)
    let precision = df?.precision || null
    return formatNumber(doc[fieldname], '', precision)
  }

  function getFormattedCurrency(fieldname, doc) {
    let currency = window.sysdefaults.currency || 'USD'
    let df = doctypeMeta[doctype]?.fields.find((f) => f.fieldname == fieldname)
    let precision = df?.precision || null

    if (df && df.options) {
      if (df.options.indexOf(':') != -1) {
        currency = currency
      } else if (doc && doc[df.options]) {
        currency = doc[df.options]
      }
    }

    return formatCurrency(doc[fieldname], '', currency, precision)
  }

  return {
    meta,
    doctypeMeta,
    getFormattedFloat,
    getFormattedPercent,
    getFormattedCurrency,
  }
}
