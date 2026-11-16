import {
  briefOlderQuery,
  briefRecordNames,
  BRIEF_OLDER_QUERY,
  BRIEF_QUERY,
} from '@/utils/brief'
import { call } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// Home's Brief links to a list of the records behind one of its counts.
// A "more" link carries the names. An "older" link has too many, so they are fetched here,
// and the list waits for them (`ready`) rather than show every record first.
export function useBriefFilter() {
  const route = useRoute()
  const router = useRouter()
  const names = computed(() => briefRecordNames(route.query))
  const older = computed(() => briefOlderQuery(route.query))
  const olderNames = ref(null)

  let latestRequest = 0
  watch(
    () => JSON.stringify(older.value),
    async () => {
      const request = ++latestRequest
      olderNames.value = null
      if (!older.value) return
      const result = await call(
        'crm.api.home.get_brief_older',
        older.value,
      ).catch(() => [])
      if (request === latestRequest) olderNames.value = result
    },
    { immediate: true },
  )

  const ready = computed(() => !older.value || olderNames.value !== null)

  const filters = computed(() => {
    if (older.value) return { name: ['in', olderNames.value || []] }
    return names.value.length ? { name: ['in', names.value] } : {}
  })
  const label = computed(() => {
    if (older.value) return __("Older than 30 days, from today's brief")
    return names.value.length ? __("From today's brief") : ''
  })

  function clear() {
    const query = { ...route.query }
    for (const key of [BRIEF_QUERY, ...BRIEF_OLDER_QUERY]) delete query[key]
    router.replace({ query })
  }

  return { filters, label, ready, clear }
}
