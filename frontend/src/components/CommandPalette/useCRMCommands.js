import { call } from 'frappe-ui'
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTelemetry } from 'frappe-ui/frappe'
import router from '@/router'
import { activeSettingsPage, showSettings } from '@/composables/settings'
import { useBroadcast } from '@/composables/useBroadcast'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { isWhatsappInstalled } from '@/composables/whatsapp'
import {
  commandPaletteOpen,
  commandPaletteQuery,
  getCommandPaletteContext,
  setCommandPaletteProvider,
} from '@/composables/useCommandPalette'
import { navigationItems } from '@/utils/navigation'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'

const RECENT_TYPES = { Lead: 'CRM Lead', Deal: 'CRM Deal' }

export function useCRMCommands() {
  const { capture } = useTelemetry()
  const { emit } = useBroadcast()
  const { showModal } = useDoctypeModal()
  const { user } = sessionStore()
  const { isManager } = usersStore()
  const state = createSearchState()
  const context = {
    capture,
    emit,
    showModal,
    user,
    isManager,
    whatsappInstalled: isWhatsappInstalled,
    state,
  }
  setCommandPaletteProvider(() => buildCommands(context))
  installWatchers(context)
}

function createSearchState() {
  return {
    records: ref([]),
    recent: ref([]),
    error: ref(false),
    requestId: 0,
    timer: null,
  }
}

function buildCommands(context) {
  const { capture, emit, showModal, isManager, whatsappInstalled, state } = context
  const tracked = trackWith(capture)
  return [
    ...navigationCommands(tracked),
    ...createCommands(tracked, emit, showModal),
    ...settingsCommands(tracked, isManager, whatsappInstalled.value),
    ...getCommandPaletteContext().map((item) => tracked(item, 'contextual')),
    ...(state.error.value ? [searchErrorCommand()] : []),
    ...state.recent.value.map((item) => recordCommand(item, 'Recent', tracked)),
    ...state.records.value.map((item) => recordCommand(item, 'Records', tracked)),
  ]
}

function trackWith(capture) {
  return (command, type) => ({
    ...command,
    perform: async () => {
      capture('command_palette_command_selected', { id: command.id, type })
      await command.perform?.()
    },
  })
}

function installWatchers(context) {
  const route = useRoute()
  watch(commandPaletteOpen, (open) => onVisibility(open, context))
  watch(commandPaletteQuery, (query) => scheduleSearch(query, context))
  watch(route, () => rememberRoute(route, context.user), { immediate: true })
  onBeforeUnmount(() => clearTimeout(context.state.timer))
}

function onVisibility(open, context) {
  if (!open) return
  context.capture('command_palette_opened')
  fetchRecords(commandPaletteQuery.value, context)
}

function scheduleSearch(query, context) {
  clearTimeout(context.state.timer)
  if (!query.trim()) return fetchRecords('', context)
  if (query.trim().length < 2) return (context.state.records.value = [])
  context.state.timer = setTimeout(() => fetchRecords(query, context), 180)
}

async function fetchRecords(query, context) {
  const currentRequest = ++context.state.requestId
  try {
    const data = await call('crm.api.command_palette.search', {
      query,
      recent_names: JSON.stringify(readRecent(context.user)),
    })
    if (currentRequest !== context.state.requestId) return
    context.state.error.value = false
    context.state.records.value = data.matches || []
    context.state.recent.value = data.recent || []
  } catch (error) {
    if (currentRequest !== context.state.requestId) return
    context.state.error.value = true
    context.state.records.value = []
    console.error('Command palette record search failed', error)
  }
}

function searchErrorCommand() {
  return {
    id: 'record-search-error',
    title: 'Record search is unavailable',
    subtitle: 'Try again shortly',
    group: 'Records',
    icon: 'circle-alert',
    disabled: true,
  }
}

function navigationCommands(tracked) {
  return navigationItems.map((item) =>
    tracked(
      {
        id: `navigate-${item.route}`,
        title: item.label,
        group: 'Navigate',
        icon: item.icon,
        keywords: `go open ${item.label}`,
        perform: () => router.push({ name: item.route }),
      },
      'navigation',
    ),
  )
}

function createCommands(tracked, emit, showModal) {
  const custom = [
    createRouteCommand('lead', 'Lead', 'Leads', 'trigger_lead_create', emit),
    createRouteCommand('deal', 'Deal', 'Deals', 'trigger_deal_create', emit),
  ]
  const generic = [
    ['contact', 'Contact', 'Contact'],
    ['organization', 'Organization', 'CRM Organization'],
    ['note', 'Note', 'FCRM Note'],
    ['task', 'Task', 'CRM Task'],
  ].map(([id, title, doctype]) => ({
    id: `create-${id}`,
    title: `Create ${title}`,
    group: 'Create',
    icon: 'plus',
    keywords: `new add ${id}`,
    perform: () => showModal({ doctype, title }),
  }))
  return [...custom, ...generic].map((item) => tracked(item, 'create'))
}

function createRouteCommand(id, title, route, event, emit) {
  return {
    id: `create-${id}`,
    title: `Create ${title}`,
    group: 'Create',
    icon: 'plus',
    keywords: `new add ${id}`,
    async perform() {
      await router.push({ name: route })
      await nextTick()
      emit(event, true)
    },
  }
}

function settingsCommands(tracked, isManager, whatsappInstalled) {
  const pages = ['Profile', 'Preferences', 'Templates', 'Telephony']
  if (isManager()) {
    pages.push('General', 'Dashboard', 'Defaults', 'Brand', 'Users', 'Invite User')
    pages.push('Sales Hierarchy', 'Accounts', 'Assignment Rules', 'SLA Policies')
    pages.push('Home Actions', 'ERPNext', 'Lead Syncing')
    if (whatsappInstalled) pages.push('WhatsApp')
  }
  return pages.map((page) =>
    tracked(
      {
        id: `settings-${page}`,
        title: page,
        group: 'Settings',
        icon: 'settings',
        keywords: `configure settings ${page}`,
        perform: () => openSettings(page),
      },
      'settings',
    ),
  )
}

function openSettings(page) {
  activeSettingsPage.value = page
  showSettings.value = true
}

function recordCommand(record, group, tracked) {
  return tracked(
    {
      id: `record-${record.doctype}-${record.name}`,
      title: record.title,
      translate: false,
      subtitle: record.doctype.replace('CRM ', ''),
      group,
      icon: 'file-text',
      rank: group === 'Recent' ? 300 : undefined,
      perform: () => router.push(recordRoute(record)),
    },
    'record',
  )
}

function recordRoute(record) {
  const param = `${record.route.toLowerCase()}Id`
  return { name: record.route, params: { [param]: record.name } }
}

function rememberRoute(route, user) {
  const doctype = RECENT_TYPES[route.name]
  if (!doctype) return
  const param = `${route.name.toLowerCase()}Id`
  const recent = readRecent(user)
  recent[doctype] = [route.params[param], ...(recent[doctype] || [])]
    .filter(Boolean)
    .filter((name, index, names) => names.indexOf(name) === index)
    .slice(0, 5)
  localStorage.setItem(recentKey(user), JSON.stringify(recent))
}

function readRecent(user) {
  try {
    return JSON.parse(localStorage.getItem(recentKey(user)) || '{}')
  } catch {
    return {}
  }
}

function recentKey(user) {
  return `crm-command-palette-recent:${user || 'anonymous'}`
}
