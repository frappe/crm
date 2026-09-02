/**
 * Client-side support for the framework's `fetch_from` docfield property.
 * The server recomputes every fetched value on save, in
 * `set_fetch_from_value` (frappe/model/base_document.py).
 */

export function getFetchSource(fetchFrom) {
  if (typeof fetchFrom !== 'string') return null

  const parts = fetchFrom.split('.')
  if (parts.length < 2) return null

  const link = parts[0]
  const source = parts[parts.length - 1]
  if (!link || !source) return null

  return { link, source }
}

export function getFieldsToFetch(fields, linkFieldname) {
  return fields.filter(
    (f) => getFetchSource(f.fetch_from)?.link === linkFieldname,
  )
}

export function getPendingFetchFields(fields, linkFieldname, doc) {
  return getFieldsToFetch(fields, linkFieldname).filter(
    (f) => !(f.fetch_if_empty && doc[f.fieldname]),
  )
}

export function getSourceFieldnames(fields) {
  return [...new Set(fields.map((f) => getFetchSource(f.fetch_from).source))]
}

// Desk locks a fetched field only while its link has a value, see
// read_only_because_of_fetch_from in frappe/public/js/frappe/form/controls/base_input.js
export function isFetchedFromLink(field, doc) {
  const link = getFetchSource(field.fetch_from)?.link
  return Boolean(link && doc[link])
}
