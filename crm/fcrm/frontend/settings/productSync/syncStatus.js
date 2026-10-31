// What the Product sync block reads from `get_product_sync_status` and the saved ERPNext CRM Settings.

import { __ } from 'frappe/i18n'

/** `run_product_sync` refuses unless the integration is on and ERPNext is on this site. */
export function canSync(saved) {
	return Boolean(saved?.enabled) && !saved?.is_erpnext_in_different_site
}

/** "12 CRM products, 9 linked to ERPNext items", or '' before the status is read. */
export function countsLine(status) {
	if (!status?.products) return ''
	const products = status.products.count ?? 0
	const linked = status.items?.count ?? 0
	return __('{0} CRM products, {1} linked to ERPNext items', [products, linked])
}

/** What has not synced yet; CRM products count only while the sync runs both ways. */
export function unsyncedLine(status) {
	const unsynced = status?.unsynced
	if (!unsynced) return ''
	const items = unsynced.items
	const products = unsynced.sync_products ? unsynced.products : 0
	if (items && products) {
		return __('{0} and {1} not yet synced', [itemCount(items), productCount(products)])
	}
	if (items) return __('{0} not yet synced', [itemCount(items)])
	if (products) return __('{0} not yet synced', [productCount(products)])
	return ''
}

function itemCount(count) {
	return count === 1 ? __('1 item') : __('{0} items', [count])
}

function productCount(count) {
	return count === 1 ? __('1 product') : __('{0} products', [count])
}
