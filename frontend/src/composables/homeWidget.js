import { usersStore } from '@/stores/users'
import { call, createResource, toast } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

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

// Briefs are kept per tab, so switching back shows the last one while it reloads.
// The tab starts empty: the first reply names the tab the user left Home on.
export function useBrief() {
  const { isManager } = usersStore()
  const tab = ref(null)
  const briefs = ref({})
  const counts = ref({})
  const brief = computed(() => briefs.value[tab.value])
  // A refresh or a doctype change makes every reply asked for before it stale.
  let generation = 0

  function load(which = tab.value) {
    const asked = generation
    return call('crm.api.home.get_brief', which ? { tab: which } : {})
      .then((reply) => {
        if (asked !== generation) return
        briefs.value[reply.tab] = reply
        counts.value[reply.tab] = reply.total
        tab.value ??= reply.tab
      })
      .catch((error) =>
        toast.error(error.messages?.[0] || __('Could not load the brief')),
      )
  }

  function loadOtherCount() {
    if (!isManager()) return
    const other = tab.value === 'team' ? 'mine' : 'team'
    const asked = generation
    call('crm.api.home.get_brief_count', { tab: other }).then((count) => {
      if (asked === generation) counts.value[other] = count
    })
  }

  function reloadAll() {
    generation++
    briefs.value = {}
    load()
    loadOtherCount()
  }

  function setTab(next) {
    tab.value = next
    load(next)
    call('crm.api.home.set_brief_tab', { tab: next })
  }

  function setDoctype(doctype) {
    call('crm.api.home.set_brief_doctype', { doctype }).then(reloadAll)
  }

  load().then(loadOtherCount)
  watch(homeVersion, reloadAll)

  return { tab, brief, counts, setTab, setDoctype }
}
