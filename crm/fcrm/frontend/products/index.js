// Product totals on CRM Lead's and CRM Deal's record pages, as CRM v1's "Product Details Script" rows do.
export const RATE_METHOD = 'crm.fcrm.doctype.crm_products.crm_products.get_product_rate_details'

/** The `products` table handlers block: a row prices itself, and the record's totals follow. */
export const productHandlers = {
	onAdd: repriceRow,
	onRemove(page) {
		updateTotals(page.doc)
	},
	async product_code(page, row) {
		const productCode = row.product_code
		const details = await page.call(RATE_METHOD, {
			product_code: productCode,
			deal: page.doctype === 'CRM Deal' && !page.isNew ? page.docname : undefined,
		})
		// A removed row throws on read; a later pick has its own handler, which prices the row for itself.
		if (!details || !page.rows('products').includes(row) || row.product_code !== productCode) return
		row.product_name = details.product_name
		row.rate = details.rate ?? 0
		repriceRow(page, row)
	},
	qty: repriceRow,
	rate: repriceRow,
	discount_percentage: repriceRow,
}

/** Sets `total` and `net_total` from the rows; a full discount keeps a net total of 0. */
export function updateTotals(doc) {
	const rows = doc.products ?? []
	const total = sum(rows, 'amount')
	const netTotal = sum(rows, 'net_amount')
	const discounted = rows.some((row) => row.discount_percentage > 0)
	doc.total = total
	doc.net_total = (netTotal || discounted) ? netTotal : total
}

/** Sets a row's `amount`, `discount_amount` and `net_amount` from its quantity, rate and discount. */
export function priceRow(row) {
	const amount = (row.qty || 0) * (row.rate || 0)
	const discount = row.discount_percentage ? (row.discount_percentage / 100) * amount : 0
	row.amount = amount
	row.discount_amount = discount
	row.net_amount = amount - discount
}

function repriceRow(page, row) {
	priceRow(row)
	updateTotals(page.doc)
}

function sum(rows, fieldname) {
	return rows.reduce((total, row) => total + (row[fieldname] || 0), 0)
}
