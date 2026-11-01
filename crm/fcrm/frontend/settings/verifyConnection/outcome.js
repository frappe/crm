// What the Verify connection block shows for the saved ERPNext connection, and the two v1 methods it asks.

import { __ } from 'frappe/i18n'

/** Errors of a request that never reached a Frappe site at the URL (requests' names and the parse of a non-Frappe page). */
const UNREACHABLE = new Set([
	'ConnectionError',
	'ConnectTimeout',
	'ReadTimeout',
	'Timeout',
	'SSLError',
	'InvalidURL',
	'InvalidSchema',
	'MissingSchema',
	'JSONDecodeError',
])

/** The saved fields a connection to another site needs, by label. */
function missingFields(saved) {
	return [
		[saved.erpnext_site_url, __('site URL')],
		[saved.api_key, __('API key')],
		[saved.api_secret, __('API secret')],
	]
		.filter(([value]) => !value)
		.map(([, label]) => label)
}

/**
 * Check the saved connection. `ask` holds the two v1 methods (`isInstalled`, `companies`);
 * the result is `{ state, title, description, companies? }`, `state` being `verified`, `wrong-url`,
 * `wrong-key`, `wrong-company` or `failed`.
 */
export async function verifyConnection(saved, ask) {
	if (!saved.is_erpnext_in_different_site) return verifyThisSite(ask)
	const missing = missingFields(saved)
	if (missing.length) {
		return failed(
			'incomplete',
			__('The connection is incomplete'),
			__('Save the {0} first.', [missing.join(', ')])
		)
	}
	let companies
	try {
		companies = (await ask.companies()).map((row) => row.company_name)
	} catch (error) {
		return explainFailure(error, saved.erpnext_site_url)
	}
	return verifyCompany(saved, companies)
}

async function verifyThisSite(ask) {
	try {
		if (await ask.isInstalled()) {
			return {
				state: 'verified',
				title: __('ERPNext is installed on this site'),
				description: '',
			}
		}
	} catch (error) {
		return failed('failed', __('Could not check this site'), error.message)
	}
	return failed(
		'wrong-site',
		__('ERPNext is not installed on this site'),
		__('Install ERPNext here, or turn on "ERPNext is in a different site" and save.')
	)
}

function verifyCompany(saved, companies) {
	const url = saved.erpnext_site_url
	if (!companies.length) {
		return failed(
			'wrong-key',
			__('{0} has no companies for this key', [url]),
			__('The site answered, but this key sees no company.')
		)
	}
	const company = saved.erpnext_company
	if (companies.includes(company)) {
		return {
			state: 'verified',
			title: __('Connected to {0}', [url]),
			description: __('Company {0} is there.', [company]),
		}
	}
	return {
		...failed(
			'wrong-company',
			company ? __('{0} is not a company on {1}', [company, url]) : __('No company is set'),
			__('The URL and keys work. Set the company to one of these:')
		),
		companies,
	}
}

function explainFailure(error, url) {
	if (UNREACHABLE.has(error.type)) {
		return failed(
			'wrong-url',
			__('Cannot reach a Frappe site at {0}', [url]),
			__('Check the site URL.')
		)
	}
	if (error.type === 'FrappeException') {
		return failed(
			'wrong-key',
			__('{0} refused the API key or secret', [url]),
			__('Or the key cannot read companies there. Check the key and secret.')
		)
	}
	return failed('failed', __('Could not verify the connection'), error.message)
}

function failed(state, title, description) {
	return { state, title, description }
}
