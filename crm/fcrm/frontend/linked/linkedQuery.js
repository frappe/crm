// What a linked-records tab reads, kept free of the desk's imports so it is unit-tested.

export function linkedQuery(source, docname) {
	const query = { fields: source.fields, filters: { [source.field]: docname }, order_by: 'modified desc' }
	// A child-table filter returns a record once per matching row.
	if (source.distinct) query.group_by = 'name'
	return query
}
