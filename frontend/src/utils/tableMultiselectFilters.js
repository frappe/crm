import { parseLinkFilters } from './fieldTransforms'

/** Keep field constraints and the selected-value exclusion as separate AND filters. */
export function tableMultiselectFilters(filters, selectedValues) {
  const parsed = parseLinkFilters(filters)
  const conditions = Array.isArray(parsed)
    ? [...parsed]
    : Object.entries(parsed || {}).map(([field, value]) =>
        Array.isArray(value) ? [field, ...value] : [field, '=', value],
      )
  return [...conditions, ['name', 'not in', [...selectedValues]]]
}
