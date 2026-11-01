// Product totals on CRM Lead's and CRM Deal's record pages, as CRM v1's "Product Details Script" rows do; free of the desk's imports so it is unit-tested.
export const RATE_METHOD = 'crm.fcrm.doctype.crm_products.crm_products.get_product_rate_details'

const PRODUCTS_KEY = 'products'

/** Whether the page's v1 "Product Details Script" row is enabled; `onRefresh` reads it first, so a field handler finds it landed. */
export function readProductDetails(page, scriptEnabled) {
	return page.cached(PRODUCTS_KEY, () => scriptEnabled(`Product Details Script for ${page.doctype}`))
}

/** The `products` table handlers block: a row prices itself, and the record's totals follow, unless the v1 row is disabled. */
export function productHandlersFor(scriptEnabled) {
	const whileEnabled =
		(handler) =>
		(page, ...args) =>
			// Read before any await: after one, the page cannot tell which script asks. A read not landed prices
			// anyway, since a skipped total is saved wrong.
			readProductDetails(page, scriptEnabled) === false ? undefined : handler(page, ...args)
	return {
		onAdd: whileEnabled(repriceRow),
		onRemove: whileEnabled((page) => updateTotals(page.doc)),
		product_code: whileEnabled(pickProduct),
		qty: whileEnabled(repriceRow),
		rate: whileEnabled(repriceRow),
		discount_percentage: whileEnabled(repriceRow),
	}
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

async function pickProduct(page, row) {
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
}

function repriceRow(page, row) {
	priceRow(row)
	updateTotals(page.doc)
}

function sum(rows, fieldname) {
	return rows.reduce((total, row) => total + (row[fieldname] || 0), 0)
}
