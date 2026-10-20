const referenceTypes = ['CRM Lead', 'CRM Deal']

// Keep both parts of a Dynamic Link: a lead and a deal can have the same name.
export function noteReferenceFilters(query) {
  if (!referenceTypes.includes(query.reference_doctype)) return {}
  const filters = { reference_doctype: query.reference_doctype }
  if (typeof query.reference_docname === 'string' && query.reference_docname) {
    filters.reference_docname = query.reference_docname
  }
  return filters
}

export function noteReferenceQuery(query, doctype, docname = '') {
  const next = { ...query }
  delete next.reference_doctype
  delete next.reference_docname
  if (referenceTypes.includes(doctype)) {
    next.reference_doctype = doctype
    if (docname) next.reference_docname = docname
  }
  return next
}
