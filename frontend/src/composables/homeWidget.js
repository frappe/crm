import { usersStore } from '@/stores/users'
import { call, createResource } from 'frappe-ui'
import { ref, watch } from 'vue'

export const homeVersion = ref(0)

export function refreshHome() {
  homeVersion.value++
}

export function useHomeWidget(widget, config = () => ({})) {
  const resource = createResource({
    url: 'crm.api.home.get_widget',
    makeParams: () => ({
      widget,
      doctype: config().doctype,
      period: config().period,
      filters: config().filters,
    }),
    auto: true,
  })
  watch(
    [
      homeVersion,
      () => config().doctype,
      () => config().period,
      () => JSON.stringify(config().filters || {}),
    ],
    () => resource.reload(),
  )
  return resource
}

export function useTabbedHomeWidget(widget, tab, config = () => ({})) {
  const resource = createResource({
    url: 'crm.api.home.get_tab',
    makeParams: () => ({
      widget,
      tab: tab.value,
      doctype: config().doctype,
    }),
    auto: true,
  })
  watch([homeVersion, tab, () => config().doctype], () => resource.reload())
  return resource
}

export function useBrief() {
  const { isManager } = usersStore()
  const tab = ref('mine')
  const counts = ref({})
  const resource = createResource({
    url: 'crm.api.home.get_brief',
    makeParams: () => ({ tab: tab.value }),
    auto: true,
    onSuccess: (brief) => (counts.value[brief.tab] = brief.total),
  })
  // A reply that lands after a quicker tab switch would show the wrong tab.
  watch([homeVersion, tab], () => {
    resource.abort()
    resource.reload()
  })

  // A tab that was left keeps the total it was showing, so only a refresh needs this.
  function loadOtherCount() {
    if (!isManager()) return
    const other = tab.value === 'team' ? 'mine' : 'team'
    const version = homeVersion.value
    call('crm.api.home.get_brief_count', { tab: other }).then((count) => {
      if (version === homeVersion.value) counts.value[other] = count
    })
  }
  loadOtherCount()
  watch(homeVersion, loadOtherCount)

  function setDoctype(doctype) {
    call('crm.api.home.set_brief_doctype', { doctype }).then(() => {
      resource.reload()
      loadOtherCount()
    })
  }

  return { tab, resource, counts, setDoctype }
}
