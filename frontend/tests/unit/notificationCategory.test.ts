import { describe, expect, it } from 'vitest'
import {
  notificationCategory,
  type CRMNotification,
} from '@/utils/notifications'

const n = (type: string, doctype: string | null = null) =>
  ({ type, notification_type_doctype: doctype }) as CRMNotification

describe('notificationCategory', () => {
  it('puts booking notifications under events', () => {
    expect(notificationCategory(n('Booking'))).toBe('events')
  })

  it('keeps the other categories', () => {
    expect(notificationCategory(n('Mention'))).toBe('mentions')
    expect(notificationCategory(n('Assignment'))).toBe('assignments')
    expect(notificationCategory(n('Reminder'))).toBe('reminders')
    expect(notificationCategory(n('Reply', 'Communication'))).toBe('emails')
    expect(notificationCategory(n('Reply', 'WA Message'))).toBe('whatsapp')
  })
})
