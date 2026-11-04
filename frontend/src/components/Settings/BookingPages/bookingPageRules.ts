// The booking page settings' rules, kept apart from the screen so they can be
// tested on their own. The server runs the same hours checks on save
// (CRM Booking Page.validate_hours); these only show them sooner.

export interface HoursRow {
  workday?: string
  start_time?: string | number
  end_time?: string | number
}

// the last time a range can end on a day, on the 15 minute grid
export const LAST_MINUTE = 23 * 60 + 45

export function hhmm(value: string | number | undefined): string {
  if (!value) return ''
  const [h, m] = String(value).split(':')
  return `${h.padStart(2, '0')}:${(m || '00').padStart(2, '0')}`
}

export function minutes(value: string | number | undefined): number {
  const [h, m] = hhmm(value).split(':').map(Number)
  return h * 60 + (m || 0)
}

export function toTime(total: number): string {
  const h = String(Math.floor(total / 60)).padStart(2, '0')
  const m = String(total % 60).padStart(2, '0')
  return `${h}:${m}`
}

export function formatClock(total: number): string {
  const h = Math.floor(total / 60)
  const m = String(total % 60).padStart(2, '0')
  return `${h % 12 || 12}:${m} ${h < 12 ? 'am' : 'pm'}`
}

export function formatDuration(total: number): string {
  if (total < 60) return __('{0} mins', [total])
  const hours = total / 60
  return hours === 1 ? __('1 hr') : __('{0} hrs', [+hours.toFixed(2)])
}

// A day's rows, earliest first. A day can have more than one, for split hours.
export function hoursFor<T extends HoursRow>(rows: T[], day: string): T[] {
  return rows
    .filter((r) => r.workday === day)
    .sort((a, b) => hhmm(a.start_time).localeCompare(hhmm(b.start_time)))
}

// The rows that break a rule, with the message to show under each
export function hoursErrors<T extends HoursRow>(
  rows: T[],
  days: string[],
): Map<T, string> {
  const errors = new Map<T, string>()
  for (const day of days) {
    let latestEnd = ''
    for (const row of hoursFor(rows, day)) {
      const start = hhmm(row.start_time)
      const end = hhmm(row.end_time)
      if (start >= end) {
        errors.set(row, __('End time must be after the start time'))
      } else if (start < latestEnd) {
        errors.set(row, __('Times overlap with another set of times'))
      }
      if (end > latestEnd) latestEnd = end
    }
  }
  return errors
}

// Like Google: end times come after the start time and show the length
export function endTimeOptions(startTime: string | number | undefined) {
  const start = minutes(startTime)
  const options = []
  for (let t = start + 15; t <= LAST_MINUTE; t += 15) {
    options.push({
      value: toTime(t),
      label: `${formatClock(t)} (${formatDuration(t - start)})`,
    })
  }
  return options
}

// A new start time; a start at or past the end pushes the end along, keeping
// the range's length
export function moveStart(
  row: HoursRow,
  value: string,
): { start_time: string; end_time?: string } {
  const length = Math.max(minutes(row.end_time) - minutes(row.start_time), 15)
  const start = Math.min(minutes(value), LAST_MINUTE - 15)
  const moved: { start_time: string; end_time?: string } = {
    start_time: `${toTime(start)}:00`,
  }
  if (start >= minutes(row.end_time)) {
    moved.end_time = `${toTime(Math.min(start + length, LAST_MINUTE))}:00`
  }
  return moved
}

// The next range on a day starts an hour after its last one ends
export function nextRange(last?: HoursRow): [string, string] {
  const from = Math.min(
    Number(hhmm(last?.end_time || '08:00').split(':')[0]) + 1,
    22,
  )
  const pad = (hour: number) => `${String(hour).padStart(2, '0')}:00:00`
  return [pad(from), pad(Math.min(from + 2, 23))]
}

// "Copy times to", like Calendly: the target days take the source day's hours
export function copyHours<T extends HoursRow>(
  rows: T[],
  day: string,
  targets: string[],
  makeRow: (day: string, start: string, end: string) => T,
): T[] {
  const source = hoursFor(rows, day)
  const to = new Set(targets.filter((d) => d !== day))
  return [
    ...rows.filter((r) => !to.has(String(r.workday))),
    ...[...to].flatMap((d) =>
      source.map((r) => makeRow(d, String(r.start_time), String(r.end_time))),
    ),
  ]
}

// mirrors ALLOWED_EMBEDDING_DOMAIN_RE in crm/www/crm_form.py, which drops anything else
const EMBEDDING_DOMAIN_RE =
  /^(https?:\/\/)?(\*\.)?[a-zA-Z0-9](?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?(?::\d+)?$/

export function invalidEmbeddingDomains(value: string | undefined): string[] {
  return (value || '')
    .split(/\s+/)
    .filter(Boolean)
    .filter((d) => !EMBEDDING_DOMAIN_RE.test(d))
}

// The embed code: the iframe, and a script that sizes it to each step, so it
// never scrolls inside
export function embedSnippet(
  url: string,
  route: string,
  title: string,
): string {
  const id = `crm-book-${route}`
  const origin = new URL(url).origin
  return [
    `<iframe id="${id}" src="${url}?embed=1" width="100%" height="720" style="border:0" title="${title || 'Book a meeting'}"></iframe>`,
    '<script>',
    '  addEventListener("message", (e) => {',
    `    if (e.origin === "${origin}" && e.data?.type === "crm-book:height" && e.data.route === "${route}")`,
    `      document.getElementById("${id}").style.height = e.data.height + "px";`,
    '  });',
    '</' + 'script>',
  ].join('\n')
}

// Where a host connects Google Calendar. The CRM has no screen for it yet, so
// it's the desk form, filled in for them.
export function googleConnectHref(
  myCalendar: string | null,
  user: string,
  fullName: string,
): string {
  if (myCalendar)
    return `/app/google-calendar/${encodeURIComponent(myCalendar)}`
  return (
    '/app/google-calendar/new?' +
    new URLSearchParams({
      user,
      calendar_name: fullName || user,
      enable: '1',
      pull_from_google_calendar: '1',
      push_to_google_calendar: '1',
    })
  )
}
