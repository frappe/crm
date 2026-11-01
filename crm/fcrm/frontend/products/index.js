// Product totals on CRM Lead's and CRM Deal's record pages, while their v1 "Product Details Script" row is enabled.
import { standardScriptEnabled } from '../form_script/standardScript.js'
import { productHandlersFor, readProductDetails } from './productTotals.js'

export function addProductDetails(page) {
	readProductDetails(page, standardScriptEnabled)
}

export const productHandlers = productHandlersFor(standardScriptEnabled)
