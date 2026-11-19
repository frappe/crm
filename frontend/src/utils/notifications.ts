export interface CRMNotification {
  creation: string
  read: 0 | 1
  type: string
  notification_type_doctype: string | null
  notification_type_doc: string | null
  reference_name: string | null
  route_name: 'Deal' | 'Lead'
  hash: string
  title: string | null
  sender: string | null
  preview: string
  from_user: { name: string; full_name: string | null }
}

export interface NotificationGroup {
  key: string
  latest: CRMNotification
  count: number
  unread: boolean
  docs: string[]
}

export type NotificationKind = 'whatsapp' | 'email' | 'reminder' | null

export function notificationKind(n: CRMNotification): NotificationKind {
  if (n.type === 'WhatsApp') return 'whatsapp'
  if (n.type === 'Reminder') return 'reminder'
  if (n.type !== 'Reply') return null
  return n.notification_type_doctype === 'WA Message' ? 'whatsapp' : 'email'
}

// Customer messages on the same record collapse into one row; everything else stays its own row.
export function groupNotifications(
  list: CRMNotification[],
): NotificationGroup[] {
  const groups = new Map<string, NotificationGroup>()
  list.forEach((n, i) => {
    const kind = notificationKind(n)
    const key =
      (kind === 'whatsapp' || kind === 'email') && n.reference_name
        ? `${n.reference_name}:${kind}`
        : String(i)
    const group = groups.get(key)
    if (!group) {
      groups.set(key, {
        key,
        latest: n,
        count: 1,
        unread: !n.read,
        docs: n.notification_type_doc ? [n.notification_type_doc] : [],
      })
      return
    }
    group.count++
    group.unread ||= !n.read
    if (n.notification_type_doc) group.docs.push(n.notification_type_doc)
  })
  return [...groups.values()]
}

export type NotificationCategory =
  | 'emails'
  | 'whatsapp'
  | 'mentions'
  | 'assignments'
  | 'reminders'
  | 'events'

export function notificationCategory(
  n: CRMNotification,
): NotificationCategory | null {
  const kind = notificationKind(n)
  if (kind === 'email') return 'emails'
  if (kind === 'whatsapp') return 'whatsapp'
  if (n.type === 'Mention') return 'mentions'
  if (n.type === 'Assignment' || n.type === 'Task') return 'assignments'
  if (n.type === 'Reminder') return 'reminders'
  if (n.type === 'Booking') return 'events'
  return null
}
