import { createResource, getCachedResource } from 'frappe-ui'

const cacheKey = (doctype, docname) => ['enrichedFields', doctype, docname]

// Fields the record's latest enrichment run wrote, as returned by
// api.get_enriched_fields. Fields the run found unchanged aren't listed.
export function useEnrichedFields(doctype, docname) {
  return createResource({
    url: 'crm.domain_enrichment.api.get_enriched_fields',
    cache: cacheKey(doctype, docname),
    params: { reference_doctype: doctype, reference_name: docname },
    auto: true,
  })
}

// Refetch after a run finishes, if the Data tab has loaded the list.
export function reloadEnrichedFields(doctype, docname) {
  getCachedResource(cacheKey(doctype, docname))?.reload()
}

// Whether `doc` still holds the value enrichment wrote. Compared as strings,
// so a Float field's 9000 matches the run's 9000.0 and null matches ''.
export function holdsEnrichedValue(doc, field) {
  return String(doc?.[field.fieldname] ?? '') === String(field.value ?? '')
}
