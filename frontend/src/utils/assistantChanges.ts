// What one assistant turn changed, as Flow reports it, turned into the one CRM page to show

export interface FlowChange {
  tool: string
  args: Record<string, any> | null
  result: any
}

// a route path in the CRM, or a Settings page opened over the current page
export type Destination =
  { path: string } | { settings: string; record?: string }

interface Touch {
  place: string
  destination: Destination | null
  record?: string
  deleted?: boolean
}

const LIST_PAGES: Record<string, string> = {
  'CRM Lead': '/leads',
  'CRM Deal': '/deals',
  Contact: '/contacts',
  'CRM Organization': '/organizations',
  'CRM Task': '/tasks',
  'FCRM Note': '/notes',
  'CRM Call Log': '/call-logs',
  'CRM Lead Status': '/leads/view/kanban',
  'CRM Deal Status': '/deals/view/kanban',
}

const RECORD_PAGES: Record<string, string> = {
  'CRM Lead': '/leads/',
  'CRM Deal': '/deals/',
  Contact: '/contacts/',
  'CRM Organization': '/organizations/',
}

// A Frappe desk address, /app/<doctype>/<name>, as the CRM page for that record, or its list
// where the CRM has no page for one record, or the Settings page that shows it. Null for what
// the CRM doesn't show.
export function crmPathFor(
  deskPath: string,
): string | { settings: string; record?: string } | null {
  const [, app, slug, ...rest] = deskPath.split('/')
  if (app !== 'app' || !slug) return null
  const named = (d: string) => d.toLowerCase().replace(/ /g, '-') === slug
  const name = decodeURIComponent(rest.join('/'))
  const settingsDoctype = Object.keys(SETTINGS_PAGES).find(named)
  if (settingsDoctype) {
    const settings = SETTINGS_PAGES[settingsDoctype]
    const opensOne = SETTINGS_RECORD_PAGES.has(settings) && name
    return opensOne ? { settings, record: name } : { settings }
  }
  const doctype = Object.keys(LIST_PAGES).find(named)
  if (!doctype) return null
  if (name && RECORD_PAGES[doctype]) {
    return RECORD_PAGES[doctype] + encodeURIComponent(name)
  }
  return LIST_PAGES[doctype]
}

const SETTINGS_PAGES: Record<string, string> = {
  'Email Account': 'Accounts',
  'Email Template': 'Templates',
  'Assignment Rule': 'Assignment Rules',
  'Web Form': 'Forms',
  'CRM Invitation': 'Invite User',
  'FCRM Settings': 'Defaults',
  'CRM Service Level Agreement': 'SLA Policies',
  'Automation Flow': 'Workflow Automations',
}

// Settings pages that open one record given its name
const SETTINGS_RECORD_PAGES = new Set(['Workflow Automations', 'Templates'])

// A reply changed what the open Settings `page` shows: reload it, and reopen the changed record
// when the page shows one at a time. Null when the page shows none of it. `label` translates a
// page's English label into the one Settings shows.
export function settingsToReload(
  changed: ChangedRecords,
  page: string,
  label: (english: string) => string = (english) => english,
): { record?: string } | null {
  if (!page) return null
  const doctype = Object.keys(SETTINGS_PAGES).find(
    (d) => label(SETTINGS_PAGES[d]) === page,
  )
  if (!doctype) return null
  if (!changed.doctypes.includes(doctype) && !changed.doctypes.includes('*')) {
    return null
  }
  const records = changed.records.filter((r) => r.doctype === doctype)
  const opensOne =
    SETTINGS_RECORD_PAGES.has(SETTINGS_PAGES[doctype]) && records.length === 1
  return opensOne ? { record: records[0].name } : {}
}

// the CRM's own setup tools for Flow (crm/flow_tools.py)
const TOOL_PAGES: Record<string, Destination> = {
  publish_web_form: { settings: 'Forms' },
  connect_email: { settings: 'Accounts' },
  invite_team: { settings: 'Invite User' },
  assign_new_leads: { settings: 'Assignment Rules' },
  set_currency: { settings: 'Defaults' },
  clear_sample_data: { path: '/leads' },
  add_automation: { settings: 'Workflow Automations' },
}

const RECORD_TOOLS = new Set(['create', 'update', 'delete', 'run_action'])

// tools that add fields to a record type (`doctype`) or show them on its page
const FIELD_TOOLS = new Set(['add_fields', 'show_fields'])

// tools that work on one lead or deal (`doctype`, `record`): an email, a note or a task on it
const WORK_TOOLS = new Set(['send_email', 'add_note', 'add_task'])

// the CRM's tools that only read; Flow reports every tool but its own lookups
const READ_TOOLS = new Set([
  'setup_status',
  'my_day',
  'sales_health',
  'find_records',
  // Flow's: a saved prompt changes nothing in the CRM
  'save_prompt',
])

// One record opens that record, several in one place open the place, and changes in
// different places open nothing, since the chat links to each.
export function whereToGo(changes: FlowChange[]): Destination | null {
  const touches = mainChanges(writes(changes)).flatMap(touchesOf)
  const places = new Set(touches.map((touch) => touch.place))
  if (places.size !== 1) return null
  const { destination } = touches[0]
  if (!destination) return null
  const records = new Set(touches.map((touch) => touch.record))
  const [record] = records
  if (records.size === 1 && record && !touches.some((touch) => touch.deleted)) {
    return { path: record }
  }
  if ('settings' in destination && destination.record) {
    // several Settings records, even from separate steps, open their list
    const settingsRecords = new Set(
      touches.map((touch) =>
        touch.destination && 'record' in touch.destination
          ? touch.destination.record
          : undefined,
      ),
    )
    if (settingsRecords.size > 1) return { settings: destination.settings }
  }
  return destination
}

// changes made along the way to the main one: fields for a form, a deal's contact and organization
const SUPPORTING_DOCTYPES = new Set([
  'Contact',
  'CRM Organization',
  'Custom Field',
  'CRM Fields Layout',
])

function writes(changes: FlowChange[]): FlowChange[] {
  return changes.filter((change) => !READ_TOOLS.has(change.tool))
}

function mainChanges(changes: FlowChange[]): FlowChange[] {
  const main = changes.filter(
    (change) =>
      !FIELD_TOOLS.has(change.tool) &&
      !SUPPORTING_DOCTYPES.has(change.args?.doctype),
  )
  // a new deal is the point; marking its lead converted is part of making it
  const madeDeal = main.some(
    (change) =>
      change.tool === 'convert_lead' ||
      (change.tool === 'create' && change.args?.doctype === 'CRM Deal'),
  )
  const kept = madeDeal
    ? main.filter(
        (change) =>
          !(change.tool === 'update' && change.args?.doctype === 'CRM Lead'),
      )
    : main
  return kept.length ? kept : changes
}

function touchesOf(change: FlowChange): Touch[] {
  if (change.tool === 'convert_lead' && change.result?.deal) {
    const record =
      RECORD_PAGES['CRM Deal'] + encodeURIComponent(change.result.deal)
    return [{ place: '/deals', destination: { path: '/deals' }, record }]
  }
  if (WORK_TOOLS.has(change.tool)) {
    const doctype = change.args?.doctype ?? ''
    const destination = destinationOf(doctype)
    const page = RECORD_PAGES[doctype]
    return [
      {
        place: destination ? placeKey(destination) : `doctype:${doctype}`,
        destination,
        record:
          page && change.args?.record
            ? page + encodeURIComponent(change.args.record)
            : undefined,
      },
    ]
  }
  if (FIELD_TOOLS.has(change.tool)) {
    // fields show on the record's page, and its list is the way there
    const destination = destinationOf(change.args?.doctype ?? '')
    const place = destination
      ? placeKey(destination)
      : `doctype:${change.args?.doctype}`
    return [{ place, destination }]
  }
  if (change.tool === 'add_automation' && change.result?.name) {
    const destination = {
      settings: 'Workflow Automations',
      record: change.result.name,
    }
    return [{ place: placeKey(destination), destination }]
  }
  if (TOOL_PAGES[change.tool]) {
    const destination = TOOL_PAGES[change.tool]
    return [{ place: placeKey(destination), destination }]
  }
  if (!RECORD_TOOLS.has(change.tool)) {
    // execute or another app's tool: something changed, but not somewhere we can show
    return [{ place: `tool:${change.tool}`, destination: null }]
  }
  const doctype = change.args?.doctype ?? ''
  const destination = destinationOf(doctype)
  const place = destination ? placeKey(destination) : `doctype:${doctype}`
  const deleted = change.tool === 'delete'
  const recordPage = !deleted && RECORD_PAGES[doctype]
  const names = namesOf(change)
  // one record on a Settings page that can show it opens there, such as a single automation
  const opensRecord =
    destination &&
    'settings' in destination &&
    SETTINGS_RECORD_PAGES.has(destination.settings) &&
    !deleted &&
    names.length === 1
  return names.map((name) => ({
    place,
    destination:
      opensRecord && name ? { ...destination, record: name } : destination,
    record: recordPage ? recordPage + encodeURIComponent(name) : undefined,
    deleted,
  }))
}

function destinationOf(doctype: string): Destination | null {
  if (SETTINGS_PAGES[doctype]) return { settings: SETTINGS_PAGES[doctype] }
  if (LIST_PAGES[doctype]) return { path: LIST_PAGES[doctype] }
  return null
}

function namesOf(change: FlowChange): string[] {
  const result = change.result ?? {}
  const names =
    {
      create: result.created,
      update: result.updated,
      delete: result.deleted,
      run_action:
        change.args?.action === 'rename' ? [result.new] : change.args?.names,
    }[change.tool] ?? []
  return names.length ? names : ['']
}

function placeKey(destination: Destination): string {
  return 'settings' in destination
    ? `settings:${destination.settings}`
    : destination.path
}

// what a CRM tool can change, so the lists showing it reload
const TOOL_DOCTYPES: Record<string, string[]> = {
  convert_lead: ['CRM Lead', 'CRM Deal', 'Contact', 'CRM Organization'],
  // setup tools: the Settings page showing what they change reloads
  publish_web_form: ['Web Form'],
  connect_email: ['Email Account'],
  invite_team: ['CRM Invitation'],
  assign_new_leads: ['Assignment Rule'],
  set_currency: ['FCRM Settings'],
  add_automation: ['Automation Flow'],
  update_task: ['CRM Task'],
  clear_sample_data: [
    'CRM Lead',
    'CRM Deal',
    'Contact',
    'CRM Organization',
    'CRM Task',
    'FCRM Note',
  ],
}

export interface ChangedRecords {
  // "*" when a step could have changed anything, such as running code
  doctypes: string[]
  records: { doctype: string; name: string }[]
}

// Every doctype and record a turn touched, so open lists and records can reload.
export function changedRecords(changes: FlowChange[]): ChangedRecords {
  const doctypes = new Set<string>()
  const records: { doctype: string; name: string }[] = []
  for (const change of writes(changes)) {
    if (RECORD_TOOLS.has(change.tool)) {
      const doctype = change.args?.doctype
      if (!doctype) continue
      doctypes.add(doctype)
      for (const name of namesOf(change)) {
        if (name) records.push({ doctype, name })
      }
    } else if (WORK_TOOLS.has(change.tool)) {
      if (change.args?.doctype && change.args?.record) {
        records.push({ doctype: change.args.doctype, name: change.args.record })
      }
      if (change.tool === 'add_task') doctypes.add('CRM Task')
      if (change.tool === 'add_note') doctypes.add('FCRM Note')
    } else if (FIELD_TOOLS.has(change.tool)) {
      if (change.args?.doctype) doctypes.add(change.args.doctype)
    } else if (TOOL_DOCTYPES[change.tool]) {
      TOOL_DOCTYPES[change.tool].forEach((doctype) => doctypes.add(doctype))
      if (change.tool === 'convert_lead' && change.args?.lead) {
        records.push({ doctype: 'CRM Lead', name: change.args.lead })
      }
    } else if (!TOOL_PAGES[change.tool]) {
      doctypes.add('*')
    }
  }
  return { doctypes: [...doctypes], records }
}
