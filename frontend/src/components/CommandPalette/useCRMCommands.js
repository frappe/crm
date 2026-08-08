import { call, dayjs, dayjsLocal } from 'frappe-ui'
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
import { getNavigationItems } from '@/utils/navigation'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import { prettyDate } from '@/utils'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'

const RECENT_TYPES = { Lead: 'CRM Lead', Deal: 'CRM Deal' }

const RECORD_ICONS = {
  'CRM Lead': LeadsIcon,
  'CRM Deal': DealsIcon,
  Contact: ContactsIcon,
  'CRM Organization': OrganizationsIcon,
}

const SETTINGS_SECTIONS = [
  {
    title: 'My settings',
    pages: [
      ['Profile', 'circle-user'],
      ['Preferences', 'sliders-horizontal'],
      ['Templates', 'notepad-text'],
      ['Telephony', 'phone'],
    ],
  },
  {
    title: 'Workspace',
    manager: true,
    pages: [
      ['General', 'settings'],
      ['Brand', 'palette'],
      ['Dashboard', 'layout-dashboard'],
      ['Defaults', 'list-checks'],
      ['Home Actions', 'house'],
    ],
  },
  {
    title: 'Team',
    manager: true,
    pages: [
      ['Users', 'users'],
      ['Invite User', 'user-plus'],
      ['Sales Hierarchy', 'network'],
      ['Assignment Rules', 'git-branch'],
    ],
  },
  {
    title: 'Integrations',
    manager: true,
    pages: [
      ['SLA Policies', 'timer'],
      ['Accounts', 'at-sign'],
      ['ERPNext', 'blocks'],
      ['Lead Syncing', 'refresh-cw'],
    ],
  },
]

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
    upcoming: ref([]),
    error: ref(false),
    requestId: 0,
    timer: null,
  }
}

function buildCommands(context) {
  const { capture, emit, showModal, isManager, whatsappInstalled, state } =
    context
  const tracked = trackWith(capture)
  return [
    ...(commandPaletteQuery.value.trim()
      ? []
      : upcomingCommands(state.upcoming.value, tracked)),
    ...navigationCommands(tracked),
    ...createCommands(tracked, emit, showModal),
    ...settingsCommands(tracked, isManager, whatsappInstalled.value),
    ...getCommandPaletteContext().map((item) => tracked(item, 'contextual')),
    ...(state.error.value ? [searchErrorCommand()] : []),
    ...state.recent.value.map((item) => recordCommand(item, 'Recent', tracked)),
    ...state.records.value.map((item) =>
      recordCommand(item, 'Records', tracked),
    ),
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
    context.state.upcoming.value = data.upcoming || []
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

function upcomingCommands(items, tracked) {
  return items.map((item) =>
    tracked(
      {
        id: `upcoming-${item.kind}-${item.name}`,
        title: item.title,
        translate: false,
        group: 'Upcoming',
        icon: item.kind === 'task' ? TaskIcon : 'timer',
        subtitle: __(item.label),
        badge: dueBadge(item.due),
        badgeClass: isOverdue(item.due) ? 'text-ink-red-5' : 'text-ink-gray-5',
        rank: 400,
        perform: () => router.push(upcomingRoute(item)),
      },
      'upcoming',
    ),
  )
}

function isOverdue(due) {
  return dayjsLocal(due).isBefore(dayjs())
}

function dueBadge(due) {
  console.log('dueBadge', due, isOverdue(due))
  const relative = prettyDate(due, true)
  return isOverdue(due) ? __('{0} overdue', [relative]) : relative
}

function upcomingRoute(item) {
  if (!item.route_name) return { name: item.route }
  const param = `${item.route.toLowerCase()}Id`
  return { name: item.route, params: { [param]: item.route_name } }
}

function navigationCommands(tracked) {
  return getNavigationItems().map((item) =>
    tracked(
      {
        id: `navigate-${item.route}`,
        title: item.label,
        group: 'Navigate',
        icon: item.icon,
        weight: 0.7,
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
  return [
    tracked(
      {
        id: 'settings',
        title: 'Settings',
        group: 'Account',
        icon: 'settings',
        keywords: 'configure preferences profile users brand telephony erpnext',
        children: () =>
          settingsChildren(tracked, isManager(), whatsappInstalled),
      },
      'settings',
    ),
  ]
}

function settingsChildren(tracked, isManager, whatsappInstalled) {
  const sections = SETTINGS_SECTIONS.filter(
    (section) => isManager || !section.manager,
  )
  const commands = sections.flatMap((section) =>
    section.pages.map(([page, icon]) =>
      settingsChild(page, icon, section.title),
    ),
  )
  if (isManager && whatsappInstalled) {
    commands.push(settingsChild('WhatsApp', 'message-circle', 'Integrations'))
  }
  return commands.map((command) => tracked(command, 'settings'))
}

function settingsChild(page, icon, group) {
  return {
    id: `settings-${page}`,
    title: page,
    group,
    icon,
    keywords: `configure settings ${page}`,
    perform: () => openSettings(page),
  }
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
      icon:
        group === 'Recent'
          ? 'clock'
          : RECORD_ICONS[record.doctype] || 'file-text',
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
