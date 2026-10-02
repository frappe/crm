import { createResource, call, toast } from 'frappe-ui'
import { reactive, computed, watch } from 'vue'

export const CONTACT_TAB_PAGE_LENGTH = 20
// Threshold: with more extra tabs than this, only the open tab loads; the others load when opened
const EAGER_LOAD_LIMIT = 3

/**
 * Extra contact tabs that installed apps declare with the `crm_contact_tabs` hook.
 * Each tab keeps its own rows, total count and loading state; rows are fetched a
 * page at a time through `crm.api.contact.get_contact_tab_rows`.
 */
export function useContactTabs(contactId, activeTab) {
  const states = reactive({})

  const tabsResource = createResource({
    url: 'crm.api.contact.get_contact_tabs',
    cache: ['contactTabs', contactId],
    params: { contact: contactId },
    auto: true,
    onSuccess(data) {
      for (const tab of data) {
        states[tab.name] ??= {
          label: tab.label,
          rows: [],
          totalCount: null,
          loading: false,
        }
      }
      const eager = data.length <= EAGER_LOAD_LIMIT
      for (const tab of data) {
        if (eager || tab.name === activeTab?.value) loadRows(tab.name)
      }
    },
  })

  const tabs = computed(() =>
    (tabsResource.data || []).map((tab) => ({
      ...tab,
      extension: true,
      count: states[tab.name]?.totalCount ?? undefined,
    })),
  )

  async function loadRows(name, { more = false } = {}) {
    const state = states[name]
    if (!state || state.loading) return
    state.loading = true
    try {
      const result = await call('crm.api.contact.get_contact_tab_rows', {
        contact: contactId,
        tab: name,
        start: more ? state.rows.length : 0,
        page_length: CONTACT_TAB_PAGE_LENGTH,
      })
      state.rows = more ? state.rows.concat(result.rows) : result.rows
      state.totalCount = result.total_count
    } catch {
      // a failing provider leaves the tab empty; one toast per tab
      if (!state.failed)
        toast.error(__('Could not load {0}', [__(state.label)]))
      state.failed = true
      if (!more) {
        state.rows = []
        state.totalCount = 0
      }
    } finally {
      state.loading = false
    }
  }

  function loadMore(name) {
    return loadRows(name, { more: true })
  }

  if (activeTab) {
    watch(activeTab, (name) => {
      if (states[name] && states[name].totalCount === null) loadRows(name)
    })
  }

  return { tabs, states, loadRows, loadMore }
}
