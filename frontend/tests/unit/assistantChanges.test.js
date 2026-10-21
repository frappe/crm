import { changedRecords, whereToGo } from '@/utils/assistantChanges'

const create = (doctype, created) => ({
  tool: 'create',
  args: { doctype },
  result: { doctype, created },
})

describe('whereToGo', () => {
  it('opens a single new lead', () => {
    expect(whereToGo([create('CRM Lead', ['CRM-LEAD-0001'])])).toEqual({
      path: '/leads/CRM-LEAD-0001',
    })
  })

  it('opens the list when several leads were added', () => {
    expect(
      whereToGo([create('CRM Lead', ['CRM-LEAD-0001', 'CRM-LEAD-0002'])]),
    ).toEqual({ path: '/leads' })
  })

  it('opens the list when leads were added across steps', () => {
    expect(
      whereToGo([
        create('CRM Lead', ['CRM-LEAD-0001']),
        create('CRM Lead', ['CRM-LEAD-0002']),
      ]),
    ).toEqual({ path: '/leads' })
  })

  it('opens the list after a delete', () => {
    expect(
      whereToGo([
        {
          tool: 'delete',
          args: { doctype: 'CRM Deal', names: ['CRM-DEAL-0001'] },
          result: { deleted: ['CRM-DEAL-0001'] },
        },
      ]),
    ).toEqual({ path: '/deals' })
  })

  it('opens the Settings page a setup step changed', () => {
    expect(
      whereToGo([
        { tool: 'assign_new_leads', args: {}, result: 'Created the rule.' },
      ]),
    ).toEqual({ settings: 'Assignment Rules' })
    expect(whereToGo([create('Email Template', ['First reply'])])).toEqual({
      settings: 'Templates',
    })
  })

  it('opens a new automation on its Settings page', () => {
    expect(
      whereToGo([
        {
          tool: 'add_automation',
          args: { name: 'Lead reply reminder' },
          result: { automation: 'Lead reply reminder', name: 'AUTO-00001' },
        },
      ]),
    ).toEqual({ settings: 'Workflow Automations', record: 'AUTO-00001' })
    expect(whereToGo([create('Automation Flow', ['AUTO-00002'])])).toEqual({
      settings: 'Workflow Automations',
      record: 'AUTO-00002',
    })
    expect(
      whereToGo([create('Automation Flow', ['AUTO-00002', 'AUTO-00003'])]),
    ).toEqual({ settings: 'Workflow Automations' })
  })

  it('opens the board after stages change', () => {
    expect(
      whereToGo([
        {
          tool: 'run_action',
          args: {
            doctype: 'CRM Deal Status',
            names: ['Ready to Close'],
            action: 'rename',
          },
          result: { new: 'Contract sent' },
        },
        create('CRM Deal Status', ['Demo']),
      ]),
    ).toEqual({ path: '/deals/view/kanban' })
  })

  it('opens the deal a lead was converted to', () => {
    expect(
      whereToGo([
        {
          tool: 'convert_lead',
          args: { lead: 'CRM-LEAD-0001' },
          result: { deal: 'CRM-DEAL-0001', link: '/crm/deals/CRM-DEAL-0001' },
        },
      ]),
    ).toEqual({ path: '/deals/CRM-DEAL-0001' })
  })

  it('opens the form, not the fields it needed', () => {
    expect(
      whereToGo([
        {
          tool: 'add_fields',
          args: { doctype: 'CRM Lead' },
          result: { added: {} },
        },
        {
          tool: 'show_fields',
          args: { doctype: 'CRM Lead' },
          result: { shown_in: [] },
        },
        { tool: 'publish_web_form', args: {}, result: { form: 'contact-us' } },
      ]),
    ).toEqual({ settings: 'Forms' })
  })

  it('opens the list of the records that got new fields', () => {
    expect(
      whereToGo([
        {
          tool: 'add_fields',
          args: { doctype: 'CRM Deal' },
          result: { added: { 'Partner type': 'partner_type' } },
        },
        {
          tool: 'show_fields',
          args: { doctype: 'CRM Deal' },
          result: { shown_in: ['side panel'], not_available: [] },
        },
      ]),
    ).toEqual({ path: '/deals' })
  })

  it('opens a new deal, not its contact, organization or lead', () => {
    expect(
      whereToGo([
        create('CRM Organization', ['Frappe']),
        create('Contact', ['Michelle Alva']),
        create('CRM Deal', ['CRM-DEAL-0001']),
        {
          tool: 'update',
          args: { doctype: 'CRM Lead', names: ['CRM-LEAD-0001'] },
          result: { updated: ['CRM-LEAD-0001'] },
        },
      ]),
    ).toEqual({ path: '/deals/CRM-DEAL-0001' })
  })

  it('opens a contact when only contacts changed', () => {
    expect(whereToGo([create('Contact', ['Michelle Alva'])])).toEqual({
      path: '/contacts/Michelle%20Alva',
    })
  })

  it('stays put when different things changed', () => {
    expect(
      whereToGo([
        create('CRM Lead', ['CRM-LEAD-0001']),
        { tool: 'invite_team', args: {}, result: 'Invited 2.' },
      ]),
    ).toBeNull()
  })

  it('stays put when it cannot show what changed', () => {
    expect(whereToGo([create('CRM Lead Source', ['Webinar'])])).toBeNull()
    expect(whereToGo([{ tool: 'execute', args: {}, result: null }])).toBeNull()
    expect(whereToGo([])).toBeNull()
  })
})

describe('changedRecords', () => {
  it('reloads the records that got new fields', () => {
    expect(
      changedRecords([
        {
          tool: 'add_fields',
          args: { doctype: 'Contact' },
          result: { added: { Birthday: 'birthday' } },
        },
      ]),
    ).toEqual({ doctypes: ['Contact'], records: [] })
  })

  it('lists the doctypes and records a reply changed', () => {
    expect(
      changedRecords([
        create('CRM Lead', ['CRM-LEAD-0001', 'CRM-LEAD-0002']),
        {
          tool: 'delete',
          args: { doctype: 'CRM Deal', names: ['CRM-DEAL-0001'] },
          result: { deleted: ['CRM-DEAL-0001'] },
        },
      ]),
    ).toEqual({
      doctypes: ['CRM Lead', 'CRM Deal'],
      records: [
        { doctype: 'CRM Lead', name: 'CRM-LEAD-0001' },
        { doctype: 'CRM Lead', name: 'CRM-LEAD-0002' },
        { doctype: 'CRM Deal', name: 'CRM-DEAL-0001' },
      ],
    })
  })

  it('covers what a CRM tool changes', () => {
    expect(
      changedRecords([
        { tool: 'convert_lead', args: { lead: 'CRM-LEAD-0001' }, result: {} },
      ]).doctypes,
    ).toEqual(['CRM Lead', 'CRM Deal', 'Contact', 'CRM Organization'])
  })

  it('reloads everything after code that could change anything', () => {
    expect(
      changedRecords([{ tool: 'execute', args: {}, result: null }]).doctypes,
    ).toEqual(['*'])
    expect(
      changedRecords([{ tool: 'invite_team', args: {}, result: {} }]).doctypes,
    ).toEqual([])
  })
})
