import { ref, computed } from 'vue'
import { createResource } from 'frappe-ui'

export function useHfrSearch() {
  const query = ref('')
  const searchBy = ref('mfl_code')
  const results = ref([])
  const panelOpen = ref(false)

  const searchResource = createResource({
    url: 'crm.api.hfr.search_facility',
    onSuccess(data) {
      results.value = data || []
    },
    onError() {
      results.value = []
    },
  })

  const detailResource = createResource({
    url: 'crm.api.hfr.get_facility_detail',
  })

  function search() {
    if ((query.value || '').length < 3) return
    results.value = []
    searchResource.submit({ query: query.value, search_by: searchBy.value || 'mfl_code' })
  }

  function selectFacility(fid, doc) {
    detailResource.submit(
      { fid },
      {
        onSuccess(data) {
          if (data) applyHfrPreview(doc, data)
        },
      },
    )
  }

  function reset() {
    query.value = ''
    results.value = []
    panelOpen.value = false
  }

  const searching = computed(() => searchResource.loading)
  const fetchingDetail = computed(() => detailResource.loading)

  return {
    query,
    searchBy,
    results,
    panelOpen,
    search,
    selectFacility,
    reset,
    searching,
    fetchingDetail,
  }
}

/**
 * Fill-empty: set a field on doc only when the current value is null/undefined/''/0.
 * doc can be the reactive frappe-ui document object or doc.doc directly.
 */
export function applyHfrPreview(doc, hfrFields) {
  const target = doc && doc.doc !== undefined ? doc.doc : doc
  if (!target || typeof target !== 'object') return
  for (const [field, value] of Object.entries(hfrFields)) {
    if (value === null || value === undefined) continue
    const current = target[field]
    if (current === null || current === undefined || current === '' || current === 0) {
      target[field] = value
    }
  }
}
