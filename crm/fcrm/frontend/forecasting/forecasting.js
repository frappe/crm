// Forecasting on CRM Deal's record page, as CRM v1's "Forecasting Script" row does; free of the desk's imports so it is unit-tested.
export const SINGLE_VALUE_METHOD = 'frappe.client.get_single_value'

const FORECASTING_KEY = 'forecasting'
const PROBABILITIES_KEY = 'probabilities:CRM Deal Status'

/** Reads FCRM Settings' switch and, when on, each deal status's probability, so the `status` handler holds them. */
export function readForecasting(page, readProbabilities) {
	const on = page.cached(FORECASTING_KEY, () =>
		page.call(SINGLE_VALUE_METHOD, { doctype: 'FCRM Settings', field: 'enable_forecasting' }),
	)
	if (on) return page.cached(PROBABILITIES_KEY, readProbabilities)
}

/** Runs `handler`, then sets `probability` from the picked status, unless the handler took the pick back. */
export function forecastProbability(handler, readProbabilities) {
	return async (page) => {
		// Read before any await: after one, the page cannot tell which script asks.
		const probabilities = readForecasting(page, readProbabilities)
		const picked = page.doc.status
		await handler(page)
		if (probabilities && page.doc.status === picked && picked in probabilities)
			page.doc.probability = probabilities[picked]
	}
}
