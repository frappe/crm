/**
 * Client-side support for the framework's `fetch_from` docfield property.
 * The server recomputes every fetched value on save, in
 * `set_fetch_from_value` (frappe/model/base_document.py).
 */

/**
 * Split a `fetch_from` into the link field it reads through and the source
 * field it reads. The last segment is the source, matching the server.
 * Returns null when there is no link field to read through.
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

/**
 * Fields whose `fetch_from` reads through the given link field.
 */
export function getFieldsToFetch(fields, linkFieldname) {
  return fields.filter(
    (f) => getFetchSource(f.fetch_from)?.link === linkFieldname,
  )
}

/**
 * Fields to fetch for a change to the given link field. A `fetch_if_empty`
 * field is left alone once it holds a value, every other field is overwritten.
 */
export function getPendingFetchFields(fields, linkFieldname, doc) {
  return getFieldsToFetch(fields, linkFieldname).filter(
    (f) => !(f.fetch_if_empty && doc[f.fieldname]),
  )
}

/**
 * Fieldnames to ask the linked doctype for, deduplicated.
 */
export function getSourceFieldnames(fields) {
  return [...new Set(fields.map((f) => getFetchSource(f.fetch_from).source))]
}

/**
 * Whether a field is currently filled by a fetch and should not be edited.
 * Desk locks a fetched field only while its link has a value, see
 * read_only_because_of_fetch_from in
 * frappe/public/js/frappe/form/controls/base_input.js
 */
export function isFetchedFromLink(field, doc) {
  const link = getFetchSource(field.fetch_from)?.link
  return Boolean(link && doc[link])
}
