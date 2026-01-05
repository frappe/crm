import { sessionStore } from '@/stores/session'
import { useControls } from './controls'
import { useList } from './list'
import { useCall } from 'frappe-ui'
import { computed, inject } from 'vue'

export function useLike() {
  const doctype = inject('doctype')
  const currentView = inject('currentView')

  const { reload } = useList()
  const { updateFilter } = useControls()
  const { user } = sessionStore()

  const isLikeFilterApplied = computed(() => {
    return currentView.value?.filters?._liked_by ? true : false
  })

  function isLiked(item) {
    if (item) {
      let likedByMe = JSON.parse(item)
      return likedByMe.includes(user)
    }
  }

  function applyLikeFilter() {
    let filters = currentView.value?.filters || {}
    if (!filters._liked_by) {
      filters['_liked_by'] = ['LIKE', `%@me%`]
    } else {
      delete filters['_liked_by']
    }
    updateFilter()
  }

  function likeDoc({ name, liked }) {
    useCall({
      url: '/api/v2/method/frappe.desk.like.toggle_like',
      method: 'POST',
      params: { doctype: doctype, name: name, add: liked ? 'No' : 'Yes' },
      onSuccess: () => reload(),
    })
  }

  return {
    isLikeFilterApplied,
    isLiked,
    applyLikeFilter,
    likeDoc,
  }
}
