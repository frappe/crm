import { applyStateFieldOptions } from '@/utils/fieldTransforms'

const stateField = { fieldname: 'state', fieldtype: 'Data', label: 'State' }
const stateOptions = { India: ['Goa', 'Kerala', 'Punjab'] }

describe('applyStateFieldOptions', () => {
  it('turns the Address state field into an Autocomplete for a known country', () => {
    const result = applyStateFieldOptions(
      stateField,
      { country: 'India' },
      'Address',
      stateOptions,
    )
    expect(result.fieldtype).toBe('Autocomplete')
    expect(result.options).toEqual(['Goa', 'Kerala', 'Punjab'])
  })

  it('prepends an out-of-list current state value so it stays visible', () => {
    const result = applyStateFieldOptions(
      stateField,
      { country: 'India', state: 'California' },
      'Address',
      stateOptions,
    )
    expect(result.options).toEqual(['California', 'Goa', 'Kerala', 'Punjab'])
  })

  it('does not duplicate a current value already in the list', () => {
    const result = applyStateFieldOptions(
      stateField,
      { country: 'India', state: 'Goa' },
      'Address',
      stateOptions,
    )
    expect(result.options).toEqual(['Goa', 'Kerala', 'Punjab'])
  })

  it('does not mutate the input field', () => {
    applyStateFieldOptions(
      stateField,
      { country: 'India' },
      'Address',
      stateOptions,
    )
    expect(stateField.fieldtype).toBe('Data')
    expect(stateField.options).toBeUndefined()
  })

  it('leaves the field unchanged when the country has no state list', () => {
    const result = applyStateFieldOptions(
      stateField,
      { country: 'France' },
      'Address',
      stateOptions,
    )
    expect(result).toBe(stateField)
  })

  it('hints to pick a country first when regional state data exists but no country is set', () => {
    const withEmptyDoc = applyStateFieldOptions(
      stateField,
      {},
      'Address',
      stateOptions,
    )
    expect(withEmptyDoc.fieldtype).toBe('Data')
    expect(withEmptyDoc.placeholder).toBe('Select Country to see state options')

    const withNullDoc = applyStateFieldOptions(
      stateField,
      null,
      'Address',
      stateOptions,
    )
    expect(withNullDoc.placeholder).toBe('Select Country to see state options')
  })

  it('does not mutate the input field when adding the country hint', () => {
    applyStateFieldOptions(stateField, {}, 'Address', stateOptions)
    expect(stateField.placeholder).toBeUndefined()
  })

  it('leaves the field unchanged when no options map is provided (app absent)', () => {
    expect(
      applyStateFieldOptions(
        stateField,
        { country: 'India' },
        'Address',
        undefined,
      ),
    ).toBe(stateField)
    expect(
      applyStateFieldOptions(stateField, { country: 'India' }, 'Address', {}),
    ).toBe(stateField)
  })

  it('only applies to the Address doctype', () => {
    const result = applyStateFieldOptions(
      stateField,
      { country: 'India' },
      'CRM Lead',
      stateOptions,
    )
    expect(result).toBe(stateField)
  })

  it('only applies to the state field', () => {
    const cityField = { fieldname: 'city', fieldtype: 'Data' }
    const result = applyStateFieldOptions(
      cityField,
      { country: 'India' },
      'Address',
      stateOptions,
    )
    expect(result).toBe(cityField)
  })

  it('handles a nullish field safely', () => {
    expect(
      applyStateFieldOptions(
        null,
        { country: 'India' },
        'Address',
        stateOptions,
      ),
    ).toBeNull()
  })
})
