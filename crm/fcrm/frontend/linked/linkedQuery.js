// What a linked-records tab reads, kept free of the desk's imports so it is unit-tested.

/** The list query for `source`'s rows that name `docname`, newest change first. */
export function linkedQuery(source, docname) {
	return { fields: source.fields, filters: { [source.field]: docname }, order_by: 'modified desc' }
}

/** Drops repeated records: a child-table filter returns a record once per matching row. */
export function uniqueRows(rows) {
	const seen = new Set()
	return rows.filter((row) => !seen.has(row.name) && seen.add(row.name))
}
