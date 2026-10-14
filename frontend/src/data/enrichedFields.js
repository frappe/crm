import { createResource, getCachedResource } from 'frappe-ui'
import { useDocument } from '@/data/document'
import { computed, inject, provide, unref } from 'vue'

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

// Provided once by the record's page so every field in its Data tab shares one
// fetch: frappe-ui reloads a cached `auto` resource each time it's created.
// The set holds the fieldnames that still hold the value enrichment wrote,
// read from the live doc so a field's icon goes away as soon as it's edited.
export function provideEnrichedFieldnames(doctype, docname) {
  const { document } = useDocument(doctype, docname)
  const enrichedFields = useEnrichedFields(doctype, docname)
  provide('enrichedFieldnames', {
    doctype,
    docname,
    fieldnames: computed(
      () =>
        new Set(
          (enrichedFields.data || [])
            .filter((field) => holdsEnrichedValue(document.doc, field))
            .map((field) => field.fieldname),
        ),
    ),
  })
}

// Empty unless the provided set is for this record, so a modal opened from the
// page (Quick Entry, a layout preview) never shows the page record's icons.
export function injectEnrichedFieldnames(doctype, docname) {
  const enriched = inject('enrichedFieldnames', null)
  return computed(() =>
    enriched &&
    enriched.doctype === unref(doctype) &&
    enriched.docname === unref(docname)
      ? enriched.fieldnames.value
      : new Set(),
  )
}
