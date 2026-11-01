// Product totals on CRM Lead's and CRM Deal's record pages, while their v1 "Product Details Script" row is enabled.
import { standardScriptEnabled } from '../form_script/standardScript.js'
import { productHandlers as handlersFor, readProductDetails } from './productTotals.js'

export function addProductDetails(page) {
	readProductDetails(page, standardScriptEnabled)
}

/** The `products` table handlers block. */
export const productHandlers = handlersFor(standardScriptEnabled)
