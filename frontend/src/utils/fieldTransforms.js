import { evaluateExpression } from '@/utils/expressions'

/**
 * Safely parse link_filters which can be a JSON string or already an object.
 * Returns the parsed filters in the `{ fieldname: [operator, value] }` form
 * expected by `frappe.desk.search.search_link`, or null.
 *
 * Frappe stores link_filters as a list of tuples
 * (`[["User", "user_type", "=", "System User"]]`), so list input is
 * converted to the mapping form — same as Desk's `parse_filters()`.
 */
export function parseLinkFilters(linkFilters) {
  if (!linkFilters) return null
  if (typeof linkFilters === 'object') return normalizeLinkFilters(linkFilters)
  try {
    return normalizeLinkFilters(JSON.parse(linkFilters))
  } catch {
    return null
  }
}

/**
 * Convert list-form link filters to the mapping form.
 * Accepts `[doctype, fieldname, operator, value]` (the stored format,
 * where `doctype` may be a dynamic-link descriptor object) or
 * `[fieldname, operator, value]`. Non-list input is returned as-is.
 *
 * `eval:` values need the current document context, which is not
 * available here, so those conditions are skipped rather than sent to
 * the server as a literal string.
 */
export function normalizeLinkFilters(linkFilters) {
  if (!Array.isArray(linkFilters)) return linkFilters

  const filters = {}
  for (const condition of linkFilters) {
    if (!Array.isArray(condition)) continue
    const [fieldname, operator, value] =
      condition.length >= 4 ? condition.slice(1) : condition
    if (!fieldname || typeof fieldname !== 'string') continue
    if (typeof value === 'string' && value.startsWith('eval:')) continue
    filters[fieldname] = [operator, value]
  }
  return filters
}

/**
 * Process a raw field meta object into a UI-ready field object.
 * Returns a NEW object — never mutates the input.
 *
 * Applies in order:
 *   1. Clone raw field
 *   2. Perm level overrides (from server layout API)
 *   3. Script property overrides (from setFieldProperty)
 *   4. Select options: string → [{label, value}] array
 *   5. Link options='User' → fieldtype='User'
 *
 * @param {object} rawField - original field meta from doctypesMeta
 * @param {object} [options]
 * @param {object} [options.permOverrides] - { fieldname: { read_only: 1 } }
 * @param {object} [options.propertyOverrides] - { fieldname: { hidden: true } }
 * @returns {object} processed field (fresh object)
 */
export function processField(rawField, options = {}) {
  if (!rawField) return null

  const { permOverrides = {}, propertyOverrides = {} } = options

  // 1. Clone
  let field = { ...rawField }

  // 2. Perm level overrides (security — from server)
  const perm = permOverrides[field.fieldname]
  if (perm) {
    Object.assign(field, perm)
  }

  // 3. Script property overrides (highest priority)
  const scriptOverride = propertyOverrides[field.fieldname]
  if (scriptOverride) {
    Object.assign(field, scriptOverride)
  }

  // 4. Select options: string → array
  if (field.fieldtype === 'Select' && typeof field.options === 'string') {
    field.options = field.options.split('\n').map((option) => ({
      label: __(option),
      value: option,
    }))

    if (field.options[0]?.value !== '' && field.reqd !== 1) {
      field.options.unshift({ label: '', value: '' })
    }
  }

  // 5. Link with options='User' → fieldtype='User'
  if (field.fieldtype === 'Link' && field.options === 'User') {
    field.fieldtype = 'User'
  }

  return field
}

/**
 * Turn the Address `state` field into a country-driven Autocomplete.
 *
 * When a regional app (e.g. India Compliance) is installed, the CRM boot exposes a
 * `{ country: [states] }` map. If the address's country has a known state list, the
 * plain-text `state` field is rendered as a searchable dropdown of those states.
 * Otherwise the field is returned unchanged (free text).
 *
 * Autocomplete (not Select) is used so a legacy free-text state value that isn't in
 * the list is still preserved. Such a value is also prepended to the options, so the
 * Combobox shows its label rather than a blank (it derives the label from options).
 *
 * If a regional app is installed but no country is picked yet (so which state list
 * applies is still unknown), the field is left as free text but gets a placeholder
 * nudging the user to pick a country first.
 *
 * @param {object} field - processed field object (from processField)
 * @param {object} doc - the document data (reads `doc.country` and `doc.state`)
 * @param {string} doctype - the field's doctype; only 'Address' is enhanced
 * @param {object} [stateOptionsByCountry] - { India: ['Goa', ...] } from the boot
 * @returns {object} the field, possibly with fieldtype='Autocomplete' + options set
 */
export function applyStateFieldOptions(
  field,
  doc,
  doctype,
  stateOptionsByCountry,
) {
  if (!field || doctype !== 'Address' || field.fieldname !== 'state') {
    return field
  }

  const states = stateOptionsByCountry?.[doc?.country]
  if (!states?.length) {
    const hasRegionalStateData =
      stateOptionsByCountry && Object.keys(stateOptionsByCountry).length > 0
    if (hasRegionalStateData && !doc?.country) {
      return {
        ...field,
        placeholder: __('Select Country to see state options'),
      }
    }
    return field
  }

  // Keep an existing out-of-list value visible (the Combobox labels by matching options).
  const current = doc?.state
  const options =
    current && !states.includes(current) ? [current, ...states] : states

  return { ...field, fieldtype: 'Autocomplete', options }
}

/**
 * Find mandatory fields that are missing values in the doc.
 * Respects script overrides for reqd and hidden.
 *
 * @param {Array} fields - raw field meta array from doctypesMeta
 * @param {object} doc - the document data
 * @param {object} [options]
 * @param {object} [options.propertyOverrides] - { fieldname: { reqd: true, hidden: false } }
 * @param {object} [options.doctypesMeta] - for resolving parent meta in mandatory_depends_on
 * @returns {string[]} array of missing field labels
 */
export function findMissingMandatory(fields, doc, options = {}) {
  if (!fields || fields.length === 0) return []
  if (!doc) return []

  const { propertyOverrides = {}, doctypesMeta = {} } = options
  const missingFields = []

  for (const df of fields) {
    const overrides = propertyOverrides[df.fieldname] || {}

    // Determine if field is hidden (script override wins)
    const isHidden =
      overrides.hidden !== undefined ? overrides.hidden : df.hidden
    if (isHidden) continue

    // Determine if field is required (script override wins)
    let isRequired
    if (overrides.reqd !== undefined) {
      isRequired = overrides.reqd
    } else if (df.reqd) {
      isRequired = true
    } else {
      let parent = doctypesMeta[df.parent] || null
      isRequired = evaluateExpression(df.mandatory_depends_on, doc, parent)
    }

    if (!isRequired) continue

    const value = doc[df.fieldname]
    if (
      value === undefined ||
      value === null ||
      (typeof value === 'string' && value.trim() === '') ||
      (Array.isArray(value) && value.length === 0)
    ) {
      missingFields.push(df.label || df.fieldname)
    }
  }

  return missingFields
}
