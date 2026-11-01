// Forecasting on CRM Deal's record page, as CRM v1's "Forecasting Script" row does; free of the desk's imports so it is unit-tested.
export const SINGLE_VALUE_METHOD = 'frappe.client.get_single_value'

export const FORECASTING_SCRIPT = 'Forecasting Script'

const FORECASTING_KEY = 'forecasting'

/** Each deal status's probability while forecasting is on and the v1 row is enabled, else `null`; one key, so one replay fetches every read. */
export function readForecasting(page, readProbabilities, scriptEnabled) {
	return page.cached(FORECASTING_KEY, async () => {
		const on = await page.call(SINGLE_VALUE_METHOD, { doctype: 'FCRM Settings', field: 'enable_forecasting' })
		return on && (await scriptEnabled(FORECASTING_SCRIPT)) ? readProbabilities() : null
	})
}

/** Runs `handler`, then sets `probability` from the picked status, unless the handler took the pick back. */
export function forecastProbability(handler, readProbabilities, scriptEnabled) {
	return async (page) => {
		// Read before any await: after one, the page cannot tell which script asks.
		const probabilities = readForecasting(page, readProbabilities, scriptEnabled)
		const picked = page.doc.status
		await handler(page)
		if (probabilities && page.doc.status === picked && Object.hasOwn(probabilities, picked))
			page.doc.probability = probabilities[picked]
	}
}

/** The `beforeSave` handler: a status changed with no `status` handler run, as a header pick saves it, sets `probability` too. */
export function forecastOnSave(readProbabilities, scriptEnabled) {
	return (page) => {
		const { status, probability } = page.doc
		// A draft that already moved `probability` (the `status` handler, or the reader) keeps it.
		if (page.isNew || status === page.saved.status || probability !== page.saved.probability) return
		const probabilities = readForecasting(page, readProbabilities, scriptEnabled)
		if (probabilities && Object.hasOwn(probabilities, status)) page.doc.probability = probabilities[status]
	}
}
