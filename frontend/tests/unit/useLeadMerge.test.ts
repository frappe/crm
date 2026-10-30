import { beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

const call = vi.fn()
// the label of the button the user clicks in the WhatsApp recipient dialog
let dialogChoice = 'Change'

vi.mock('frappe-ui', () => ({ call: (...args: unknown[]) => call(...args) }))
vi.mock('@/utils/dialogs', () => ({
  createDialog: (options: {
    actions: { label: string; onClick: (ctx: { close: () => void }) => void }[]
  }) => {
    const dialog = reactive({ show: true })
    const close = () => (dialog.show = false)
    setTimeout(() =>
      options.actions.find((a) => a.label === dialogChoice)!.onClick({ close }),
    )
    return dialog
  },
}))
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
    dialogChoice = 'Change'
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

  describe('when the target has a WhatsApp conversation with its mobile_no', () => {
    const refusal = {
      exc_type: 'WhatsAppRecipientChangeError',
      messages: ['This lead has 2 WhatsApp message(s) with +1 555 0199.'],
    }

    beforeEach(() => {
      const loadFields = call.getMockImplementation()!
      call.mockImplementation(
        async (method: string, params: Record<string, unknown>) => {
          if (
            method === 'crm.api.lead.merge_leads' &&
            !params.confirm_whatsapp_recipient_change
          ) {
            throw refusal
          }
          return loadFields(method)
        },
      )
    })

    it('asks the user and retries the merge with their confirmation', async () => {
      const merge = useLeadMerge('CRM-LEAD-0001', 'CRM-LEAD-0002', [])
      await merge.load()
      merge.pick('email', 'source')

      expect(await merge.merge()).toBe('CRM-LEAD-0001')
      expect(call).toHaveBeenLastCalledWith('crm.api.lead.merge_leads', {
        target: 'CRM-LEAD-0001',
        source: 'CRM-LEAD-0002',
        take_from_source: ['email'],
        confirm_whatsapp_recipient_change: 1,
      })
      expect(merge.error.value).toBe('')
    })

    it('does not merge or show an error when the user cancels', async () => {
      dialogChoice = 'Cancel'
      const merge = useLeadMerge('CRM-LEAD-0001', 'CRM-LEAD-0002', [])
      await merge.load()

      expect(await merge.merge()).toBeNull()
      const mergeCalls = call.mock.calls.filter(
        ([m]) => m === 'crm.api.lead.merge_leads',
      )
      expect(mergeCalls).toHaveLength(1)
      expect(merge.error.value).toBe('')
    })
  })
})
