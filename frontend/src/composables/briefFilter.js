import {
  briefListQuery,
  briefRecordNames,
  BRIEF_LIST_QUERY,
  BRIEF_QUERY,
  OLDER_LISTS,
} from '@/utils/brief'
import { call } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// Home's Brief links to a list of the records behind one of its counts.
// A "more" link carries the names. Other links can have too many, so they are fetched here,
// and the list waits for them (`ready`) rather than show every record first.
export function useBriefFilter() {
  const route = useRoute()
  const router = useRouter()
  const names = computed(() => briefRecordNames(route.query))
  const list = computed(() => briefListQuery(route.query))
  const listNames = ref(null)

  let latestRequest = 0
  watch(
    () => JSON.stringify(list.value),
    async () => {
      const request = ++latestRequest
      listNames.value = null
      if (!list.value) return
      const result = await call(
        'crm.api.home.get_brief_records',
        list.value,
      ).catch(() => [])
      if (request === latestRequest) listNames.value = result
    },
    { immediate: true },
  )

  const ready = computed(() => !list.value || listNames.value !== null)

  const filters = computed(() => {
    if (list.value) return { name: ['in', listNames.value || []] }
    return names.value.length ? { name: ['in', names.value] } : {}
  })
  const label = computed(() => {
    if (OLDER_LISTS.includes(list.value?.kind))
      return __("Older than 30 days, from today's brief")
    return list.value || names.value.length ? __("From today's brief") : ''
  })

  function clear() {
    const query = { ...route.query }
    for (const key of [BRIEF_QUERY, ...BRIEF_LIST_QUERY]) delete query[key]
    router.replace({ query })
  }

  return { filters, label, ready, clear }
}
