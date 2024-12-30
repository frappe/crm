import { createResource } from 'frappe-ui'
import { formatCurrency, formatNumber } from '@/utils/numberFormat.js'
import { ref, reactive } from 'vue'

const doctypeMeta = reactive({})
const userSettings = reactive({})

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

      userSettings[doctype] = JSON.parse(res.user_settings)
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

  function getGridSettings(parentDoctype, dt = null) {
    dt = dt || doctype
    if (!userSettings[parentDoctype]?.['GridView']?.[doctype]) return {}
    return userSettings[parentDoctype]['GridView'][doctype]
  }

  function getFields(dt = null) {
    dt = dt || doctype
    return doctypeMeta[dt]?.fields.map((f) => {
      if (f.fieldtype === 'Select' && typeof f.options === 'string') {
        f.options = f.options.split('\n').map((option) => {
          return {
            label: option,
            value: option,
          }
        })
      }
      return f
    })
  }

  function saveUserSettings(parentDoctype, key, value, callback) {
    let oldUserSettings = userSettings[parentDoctype]
    let newUserSettings = JSON.parse(JSON.stringify(oldUserSettings))

    if (newUserSettings[key] === undefined) {
      newUserSettings[key] = { [doctype]: value }
    } else {
      newUserSettings[key][doctype] = value
    }

    if (JSON.stringify(oldUserSettings) !== JSON.stringify(newUserSettings)) {
      return createResource({
        url: 'frappe.model.utils.user_settings.save',
        params: {
          doctype: parentDoctype,
          user_settings: JSON.stringify(newUserSettings),
        },
        auto: true,
        onSuccess: () => callback?.(),
      })
    }
    return callback?.()
  }

  return {
    meta,
    doctypeMeta,
    userSettings,
    getFields,
    getGridSettings,
    saveUserSettings,
    getFormattedFloat,
    getFormattedPercent,
    getFormattedCurrency,
  }
}
