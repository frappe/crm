import { getMeta } from '@/stores/meta'
import { createResource, toast } from 'frappe-ui'
import { ref, computed } from 'vue'

const store = {}

export function useQuickFilters(doctype) {
  if (!store[doctype]) {
    store[doctype] = createState(doctype)
  }
  return store[doctype]
}

function createState(doctype) {
  const customizeQuickFilter = ref(false)
  const newQuickFilters = ref([])

  const { getFields } = getMeta(doctype)

  const quickFilters = createResource({
    url: 'crm.api.doc.get_quick_filters',
    params: { doctype: doctype },
    cache: ['Quick Filters', doctype],
    onSuccess(filters) {
      setupQuickFilters(filters)
    },
  })

  if (!quickFilters.data) quickFilters.fetch()

  function showCustomizeQuickFilter() {
    customizeQuickFilter.value = true
    setupQuickFilters(quickFilters.data)
  }

  function addQuickFilter(f) {
    if (!newQuickFilters.value.some((filter) => filter.fieldname === f.value)) {
      newQuickFilters.value.push({
        label: f.label,
        fieldname: f.value,
        fieldtype: f.fieldtype,
      })
    }
  }

  function removeQuickFilter(f) {
    newQuickFilters.value = newQuickFilters.value.filter(
      (filter) => filter.fieldname !== f.fieldname,
    )
  }

  const updateQuickFilters = createResource({
    url: 'crm.api.doc.update_quick_filters',
    onSuccess() {
      customizeQuickFilter.value = false

      quickFilters.update({ params: { doctype: doctype, cached: false } })
      quickFilters.reload()
      toast.success(__('Quick Filters updated successfully'))
    },
  })

  function saveQuickFilters() {
    let new_filters =
      newQuickFilters.value?.map((filter) => filter.fieldname) || []
    let old_filters = quickFilters.data?.map((filter) => filter.fieldname) || []

    updateQuickFilters.update({
      params: {
        quick_filters: JSON.stringify(new_filters),
        old_filters: JSON.stringify(old_filters),
        doctype: doctype,
      },
    })

    updateQuickFilters.fetch()
  }

  const quickFilterOptions = computed(() => {
    let fields = getFields()
    if (!fields) return []

    let existingQuickFilters = newQuickFilters.value.map((f) => f.fieldname)
    let restrictedFieldtypes = [
      'Tab Break',
      'Section Break',
      'Column Break',
      'Table',
      'Table MultiSelect',
      'HTML',
      'Button',
      'Image',
      'Fold',
      'Heading',
    ]
    let options = fields
      .filter((f) => f.label && !restrictedFieldtypes.includes(f.fieldtype))
      .filter((f) => !existingQuickFilters.includes(f.fieldname))
      .map((field) => ({
        label: field.label,
        value: field.fieldname,
        fieldtype: field.fieldtype,
      }))

    if (!options.some((f) => f.fieldname === 'name')) {
      options.push({
        label: __('Name'),
        value: 'name',
        fieldtype: 'Data',
      })
    }

    return options
  })

  const quickFilterList = computed(() => {
    let filters = quickFilters.data || []

    filters.forEach((filter) => {
      filter['value'] = filter.fieldtype == 'Check' ? false : ''
      if (list.value?.params?.filters[filter.fieldname]) {
        let value = list.value?.params.filters[filter.fieldname]
        if (Array.isArray(value)) {
          if (
            (['Check', 'Select', 'Link', 'Date', 'Datetime'].includes(
              filter.fieldtype,
            ) &&
              value[0]?.toLowerCase() == 'like') ||
            value[0]?.toLowerCase() != 'like'
          )
            return
          filter['value'] = value[1]?.replace(/%/g, '')
        } else if (typeof value == 'boolean') {
          filter['value'] = value
        } else {
          filter['value'] = value?.replace(/%/g, '')
        }
      }
    })

    return filters
  })

  function setupQuickFilters(filters) {
    newQuickFilters.value = filters.map((f) => ({
      label: f.label,
      fieldname: f.fieldname,
      fieldtype: f.fieldtype,
    }))
  }

  function applyQuickFilter(filter, value) {
    let filters = { ...list.value?.params.filters }
    let field = filter.fieldname
    if (value) {
      if (
        ['Check', 'Select', 'Link', 'Date', 'Datetime'].includes(
          filter.fieldtype,
        )
      ) {
        filters[field] = value
      } else {
        filters[field] = ['LIKE', `%${value}%`]
      }
      filter['value'] = value
    } else {
      delete filters[field]
      filter['value'] = ''
    }
    updateFilter(filters)
  }

  return {
    customizeQuickFilter,
    newQuickFilters,
    quickFilterOptions,
    quickFilterList,
    addQuickFilter,
    removeQuickFilter,
    saveQuickFilters,
    showCustomizeQuickFilter,
    updateQuickFilters,
    applyQuickFilter,
  }
}
