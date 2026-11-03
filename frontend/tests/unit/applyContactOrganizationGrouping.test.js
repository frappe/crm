import { applyContactOrganizationGrouping } from '@/utils/fieldTransforms'

const contactField = {
  fieldname: 'contact',
  fieldtype: 'Link',
  options: 'Contact',
  label: 'Contact',
}

describe('applyContactOrganizationGrouping', () => {
  it('groups the contact field by the deal organization', () => {
    const result = applyContactOrganizationGrouping(
      contactField,
      { organization: 'Frappe' },
      'CRM Deal',
    )
    expect(result.grouping).toEqual({
      filters: { company_name: 'Frappe' },
      label: 'Contacts at Frappe',
      otherLabel: 'Other contacts',
    })
  })

  it('leaves link_filters alone so no contact is filtered out', () => {
    const fieldWithFilters = {
      ...contactField,
      link_filters: JSON.stringify({ status: 'Passive' }),
    }
    const result = applyContactOrganizationGrouping(
      fieldWithFilters,
      { organization: 'Frappe' },
      'CRM Deal',
    )
    expect(result.link_filters).toBe(fieldWithFilters.link_filters)
  })

  it('does not group when no organization is selected', () => {
    const result = applyContactOrganizationGrouping(
      contactField,
      { organization: '' },
      'CRM Deal',
    )
    expect(result).toBe(contactField)
  })

  it('does not group when the doc is missing', () => {
    const result = applyContactOrganizationGrouping(
      contactField,
      null,
      'CRM Deal',
    )
    expect(result).toBe(contactField)
  })

  it('does not mutate the input field', () => {
    applyContactOrganizationGrouping(
      contactField,
      { organization: 'Frappe' },
      'CRM Deal',
    )
    expect(contactField.grouping).toBeUndefined()
  })

  it('only applies to the CRM Deal doctype', () => {
    const result = applyContactOrganizationGrouping(
      contactField,
      { organization: 'Frappe' },
      'CRM Lead',
    )
    expect(result).toBe(contactField)
  })

  it('only applies to the contact fieldname', () => {
    const otherField = { ...contactField, fieldname: 'primary_contact' }
    const result = applyContactOrganizationGrouping(
      otherField,
      { organization: 'Frappe' },
      'CRM Deal',
    )
    expect(result).toBe(otherField)
  })

  it('only applies to a Link field with options Contact', () => {
    const wrongOptions = { ...contactField, options: 'User' }
    const result = applyContactOrganizationGrouping(
      wrongOptions,
      { organization: 'Frappe' },
      'CRM Deal',
    )
    expect(result).toBe(wrongOptions)
  })

  it('handles a nullish field safely', () => {
    expect(
      applyContactOrganizationGrouping(
        null,
        { organization: 'Frappe' },
        'CRM Deal',
      ),
    ).toBeNull()
  })
})
