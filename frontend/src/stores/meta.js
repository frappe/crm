import { createResource } from 'frappe-ui'
import { formatCurrency, formatNumber } from '@/utils/numberFormat.js'
import { computed, reactive } from 'vue'

const standardFieldsMeta = [
  {
    fieldname: 'name',
    label: 'Name',
    fieldtype: 'Data',
  },
  {
    fieldname: 'creation',
    label: 'Created On',
    fieldtype: 'Datetime',
  },
  {
    fieldname: 'modified',
    label: 'Last Modified',
    fieldtype: 'Datetime',
  },
  {
    fieldname: 'modified_by',
    label: 'Modified By',
    fieldtype: 'Link',
    options: 'User',
  },
  { label: 'Assigned To', fieldtype: 'Text', fieldname: '_assign' },
  {
    label: 'Owner',
    fieldtype: 'Link',
    fieldname: 'owner',
    options: 'User',
  },
  { label: 'Like', fieldtype: 'Data', fieldname: '_liked_by' },
]

const doctypesMeta = reactive({})
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
        doctypesMeta[dtMeta.name] = dtMeta
      }

      userSettings[doctype] = JSON.parse(res.user_settings)
    },
  })

  const doctypeMeta = computed(() => doctypesMeta[doctype] || null)

  if (!doctypesMeta[doctype] && !meta.loading) {
    meta.fetch()
  }

  function getFormattedPercent(fieldname, doc) {
    let value = getFormattedFloat(fieldname, doc)
    return value + '%'
  }

  function getFormattedFloat(fieldname, doc) {
    let df = doctypesMeta[doctype]?.fields.find((f) => f.fieldname == fieldname)
    let precision = df?.precision || null
    return formatNumber(doc[fieldname], '', precision)
  }

  function getFloatWithPrecision(fieldname, doc) {
    let df = doctypesMeta[doctype]?.fields.find((f) => f.fieldname == fieldname)
    let precision = df?.precision || null
    return formatNumber(doc[fieldname], '', precision)
  }

  function getCurrencyWithPrecision(fieldname, doc) {
    let df = doctypesMeta[doctype]?.fields.find((f) => f.fieldname == fieldname)
    let precision = df?.precision || null
    return formatCurrency(doc[fieldname], '', '', precision)
  }

  function getFormattedCurrency(fieldname, doc, parentDoc = null) {
    let currency = window.sysdefaults.currency || 'USD'
    let df = doctypesMeta[doctype]?.fields.find((f) => f.fieldname == fieldname)
    let precision = df?.precision || null

    if (df && df.options) {
      if (df.options.indexOf(':') != -1) {
        // TODO: Handle this case
      } else if (doc && doc[df.options]) {
        currency = doc[df.options]
      } else if (parentDoc && parentDoc[df.options]) {
        currency = parentDoc[df.options]
      }
    }

    return formatCurrency(doc[fieldname], '', currency, precision)
  }

  function getGridSettings() {
    return doctypeMeta.value || {}
  }

  function getGridViewSettings(parentDoctype) {
    if (!userSettings[parentDoctype]?.['GridView']?.[doctype]) return {}
    return userSettings[parentDoctype]['GridView'][doctype]
  }

  function getFields(dt = null, withStandardFields = false) {
    dt = dt || doctype
    let fieldsMeta =
      doctypesMeta[dt]?.fields.map((f) => {
        if (f.fieldtype === 'Select' && typeof f.options === 'string') {
          f.options = f.options.split('\n').map((option) => {
            return {
              label: option,
              value: option,
            }
          })

          if (f.options[0]?.value !== '' && f.reqd !== 1) {
            f.options.unshift({
              label: '',
              value: '',
            })
          }
        }
        if (f.fieldtype === 'Link' && f.options == 'User') {
          f.fieldtype = 'User'
        }
        return f
      }) || []

    if (withStandardFields) {
      fieldsMeta = fieldsMeta.concat(standardFieldsMeta)
    }

    return fieldsMeta || []
  }

  function saveUserSettings(parentDoctype, key, value, callback) {
    let oldUserSettings = userSettings[parentDoctype] || {}
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
        onSuccess: () => {
          userSettings[parentDoctype] = newUserSettings
          callback?.()
        },
      })
    }
    userSettings[parentDoctype] = newUserSettings
    return callback?.()
  }

  function isTranslatable(dt = null) {
    dt = dt || doctype
    let meta = doctypesMeta[dt]
    return meta && meta.translated_doctype
  }

  return {
    meta,
    doctypeMeta,
    doctypesMeta,
    userSettings,
    getFields,
    getGridSettings,
    getGridViewSettings,
    saveUserSettings,
    getFloatWithPrecision,
    getCurrencyWithPrecision,
    getFormattedFloat,
    getFormattedPercent,
    getFormattedCurrency,
    isTranslatable,
  }
}
