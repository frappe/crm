// What one assistant turn changed, as Flow reports it, turned into the one CRM page to show

export interface FlowChange {
  tool: string
  args: Record<string, any> | null
  result: any
}

// a route path in the CRM, or a Settings page opened over the current page
export type Destination = { path: string } | { settings: string }

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

const SETTINGS_PAGES: Record<string, string> = {
  'Email Account': 'Accounts',
  'Email Template': 'Templates',
  'Assignment Rule': 'Assignment Rules',
  'Web Form': 'Forms',
  'CRM Invitation': 'Invite User',
  'FCRM Settings': 'Defaults',
  'CRM Service Level Agreement': 'SLA Policies',
}

// the CRM's own setup tools for Flow (crm/flow_tools.py)
const TOOL_PAGES: Record<string, Destination> = {
  publish_web_form: { settings: 'Forms' },
  connect_email: { settings: 'Accounts' },
  invite_team: { settings: 'Invite User' },
  assign_new_leads: { settings: 'Assignment Rules' },
  set_currency: { settings: 'Defaults' },
  clear_sample_data: { path: '/leads' },
}

const RECORD_TOOLS = new Set(['create', 'update', 'delete', 'run_action'])

// tools that add fields to a record type (`doctype`) or show them on its page
const FIELD_TOOLS = new Set(['add_fields', 'show_fields'])

// One record opens that record, several in one place open the place, and changes in
// different places open nothing, since the chat links to each.
export function whereToGo(changes: FlowChange[]): Destination | null {
  const touches = mainChanges(changes).flatMap(touchesOf)
  const places = new Set(touches.map((touch) => touch.place))
  if (places.size !== 1) return null
  const { destination } = touches[0]
  if (!destination) return null
  const records = new Set(touches.map((touch) => touch.record))
  const [record] = records
  if (records.size === 1 && record && !touches.some((touch) => touch.deleted)) {
    return { path: record }
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
  if (FIELD_TOOLS.has(change.tool)) {
    // fields show on the record's page, and its list is the way there
    const destination = destinationOf(change.args?.doctype ?? '')
    const place = destination
      ? placeKey(destination)
      : `doctype:${change.args?.doctype}`
    return [{ place, destination }]
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
  return namesOf(change).map((name) => ({
    place,
    destination,
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
  for (const change of changes) {
    if (RECORD_TOOLS.has(change.tool)) {
      const doctype = change.args?.doctype
      if (!doctype) continue
      doctypes.add(doctype)
      for (const name of namesOf(change)) {
        if (name) records.push({ doctype, name })
      }
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
