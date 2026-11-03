import { describe, expect, it, vi } from 'vitest'

const runMethod = vi.fn().mockResolvedValue({ data: null })
vi.mock('@framework/ui/api', () => ({ runMethod }))

describe('callApi', () => {
  it('sends a CRM Task name, a number, to link_to_call_log as a string', async () => {
    const { callApi } = await import('../../../crm/fcrm/frontend/telephony/callApi.js')
    await callApi.link('CA1', 'CRM Task', 29)
    expect(runMethod).toHaveBeenCalledWith('crm.integrations.api.link_to_call_log', {
      call_sid: 'CA1',
      doctype: 'CRM Task',
      docname: '29',
    }, undefined)
  })
})
