import { ref, watchEffect } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { toValue } from '@vueuse/core'
import { usersStore } from '@/stores/users'

const operatorMap = {
  is: '=',
  'is not': '!=',
  equals: '=',
  'not equals': '!=',
  yes: true,
  no: false,
  like: 'LIKE',
  'not like': 'NOT LIKE',
  '>': '>',
  '<': '<',
  '>=': '>=',
  '<=': '<=',
}

export function useFilter(fields) {
  const route = useRoute()
  const router = useRouter()
  const { getUser } = usersStore()
  const storage = ref(new Set())

  watchEffect(() => {
    const f__ = toValue(fields)
    if (fields && !f__) return
    storage.value = new Set()
    const q = route.query.q || ''
    q.split(' ')
      .map((f) => {
        const [fieldname, operator, value] = f
          .split(':')
          .map(decodeURIComponent)
        const field = (f__ || []).find((f) => f.fieldname === fieldname)
        return {
          field,
          fieldname,
          operator,
          value,
        }
      })
      .filter((f) => !f__ || (f__ && f.field))
      .filter((f) => operatorMap[f.operator])
      .forEach((f) => storage.value.add(f))
  })

  function getArgs(old) {
    old = old || {}
    const l__ = Array.from(storage.value)
    const obj = l__.map(transformIn).reduce((p, c) => {
      p[c.fieldname] = [operatorMap[c.operator.toLowerCase()], c.value]
      return p
    }, {})
    const merged = { ...old, ...obj }
    return merged
  }

  function apply(r) {
    r = r || route
    const l__ = Array.from(storage.value)
    const q = l__
      .map(transformOut)
      .map((f) =>
        [f.fieldname, f.operator.toLowerCase(), f.value]
          .map(encodeURIComponent)
          .join(':')
      )
      .join(' ')
    if (!q && !r.query.q) {
      router.push({ ...r, query: { ...r.query } })
    } else {
      router.push({ ...r, query: { ...r.query, q } })
    }
  }

  /**
   * Used to set fields internally. These will not reflect in URL.
   * Can be used for APIs
   */
  function transformIn(f) {
    if (f.fieldname === '_assign') {
      f.operator = f.operator === 'is' ? 'like' : 'not like'
    }
    if (f.operator.includes('like') && !f.value.includes('%')) {
      f.value = `%${f.value}%`
    }
    return f
  }

  /**
   * Used to set fields in URL query
   */
  function transformOut(f) {
    if (f.value === '@me') {
      f.value = getUser()
    }
    return f
  }

  return { apply, getArgs, storage }
}
