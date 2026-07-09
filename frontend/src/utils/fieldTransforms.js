import { evaluateExpression } from '@/utils/expressions'

/**
 * Safely parse link_filters which can be a JSON string or already an object.
 * Returns the parsed object or null.
 */
export function parseLinkFilters(linkFilters) {
  if (!linkFilters) return null
  if (typeof linkFilters === 'object') return linkFilters
  try {
    return JSON.parse(linkFilters)
  } catch {
    return null
  }
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
      label: option,
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
  if (!states?.length) return field

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
