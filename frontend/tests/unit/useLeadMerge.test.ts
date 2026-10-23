import { beforeEach, describe, expect, it, vi } from 'vitest'

const call = vi.fn()

vi.mock('frappe-ui', () => ({ call: (...args: unknown[]) => call(...args) }))
vi.mock('@/stores/users', () => ({
  usersStore: () => ({ getUser: (name: string) => ({ full_name: name }) }),
}))

import { useLeadMerge } from '@/composables/useLeadMerge'

const field = (
  fieldname: string,
  source_value: unknown,
  target_value: unknown,
) => ({
  fieldname,
  label: fieldname,
  fieldtype: 'Data',
  options: null,
  source_value,
  target_value,
  source_display: String(source_value ?? ''),
  target_display: String(target_value ?? ''),
})

describe('useLeadMerge', () => {
  beforeEach(() => {
    call.mockReset()
    call.mockImplementation(async (method: string) => {
      if (method === 'crm.api.lead.get_lead_merge_fields') {
        return [
          field('email', 'a@example.com', 'b@example.com'),
          field('mobile_no', '+1 555 0100', ''),
          field('website', 'a.example.com', 'b.example.com'),
        ]
      }
      if (method === 'crm.api.doc.get_assigned_users') return []
      return { target: 'CRM-LEAD-0001' }
    })
  })

  it('sends only the conflicts picked from the source, not fields empty on the target', async () => {
    const merge = useLeadMerge('CRM-LEAD-0001', 'CRM-LEAD-0002', [])
    await merge.load()
    merge.pick('email', 'source')

    await merge.merge()

    expect(call).toHaveBeenLastCalledWith('crm.api.lead.merge_leads', {
      target: 'CRM-LEAD-0001',
      source: 'CRM-LEAD-0002',
      take_from_source: ['email'],
    })
  })
})
