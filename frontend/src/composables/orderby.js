import { useRoute, useRouter } from 'vue-router'

export function useOrderBy() {
  const route = useRoute()
  const router = useRouter()

  function get() {
    const q = route.query.sort ?? ''
    const d = decodeURIComponent(q)
    return d
  }

  function set(sort, r) {
    r = r || route
    const q = encodeURIComponent(sort)
    router.push({ ...r, query: { ...r.query, sort: q } })
  }

  return {
    get,
    set,
  }
}
