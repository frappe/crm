export const DONT_IMPORT = "Don't Import"
export const LEAD_NAME_FIELD = 'first_name'

export function getColumnMappings(preview) {
  return (preview?.columns || []).slice(1).map((column, index) => ({
    index,
    header: column.header_title,
    fieldname: column.skip_import ? '' : column.df?.fieldname || '',
  }))
}

export function toColumnToFieldMap(mappings) {
  return Object.fromEntries(
    mappings.map((m) => [String(m.index), m.fieldname || DONT_IMPORT]),
  )
}

export function getUnmappedRequiredFields(fields, mappings) {
  const mapped = new Set(mappings.map((m) => m.fieldname).filter(Boolean))
  return fields.filter((f) => f.reqd && !f.default && !mapped.has(f.fieldname))
}

export function isLeadNameMapped(mappings) {
  return mappings.some((m) => m.fieldname === LEAD_NAME_FIELD)
}

export function groupInvitesByRole(rows) {
  const groups = {}
  const seen = new Set()
  for (const row of rows) {
    const email = row.email?.trim().toLowerCase()
    if (!email || seen.has(email)) continue
    seen.add(email)
    ;(groups[row.role] ||= []).push(email)
  }
  return groups
}

export function stripTags(html) {
  return String(html || '').replace(/<[^>]*>/g, '')
}

export function describeFailedRow(log) {
  const row = parseJSON(log.row_indexes)?.[0]
  const message = parseJSON(log.messages)?.[0]?.message
  return {
    row: row ? row - 1 : null,
    message: stripTags(message) || __('Failed to import'),
  }
}

function parseJSON(value) {
  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}
