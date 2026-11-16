import { briefRecordNames, BRIEF_QUERY } from '@/utils/brief'
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// Home's Brief links to a list with the records it had no room to show.
export function useBriefFilter() {
  const route = useRoute()
  const router = useRouter()
  const names = computed(() => briefRecordNames(route.query))

  const filters = computed(() =>
    names.value.length ? { name: ['in', names.value] } : {},
  )
  const label = computed(() =>
    names.value.length ? __("From today's brief") : '',
  )

  function clear() {
    const query = { ...route.query }
    delete query[BRIEF_QUERY]
    router.replace({ query })
  }

  return { filters, label, clear }
}
