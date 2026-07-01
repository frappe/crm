import * as fs from 'fs'
import { APIRequestContext } from '@playwright/test'

/**
 * Frappe API response wrapper.
 */
export interface FrappeResponse<T = unknown> {
	message?: T
	exc?: string
	exc_type?: string
	_server_messages?: string
}

// CSRF token file saved by auth.setup.ts
const CSRF_FILE = 'e2e/.auth/csrf.json'

let csrfTokenCache: string | null = null

/**
 * Read the CSRF token saved during auth setup (from window.frappe.csrf_token).
 */
function getCsrfToken(): string {
	if (csrfTokenCache !== null) {
		return csrfTokenCache
	}

	try {
		if (fs.existsSync(CSRF_FILE)) {
			const data = JSON.parse(fs.readFileSync(CSRF_FILE, 'utf-8'))
			csrfTokenCache = data.csrf_token || ''
			return csrfTokenCache
		}
	} catch (error) {
		console.warn('Failed to read CSRF token file:', error)
	}

	csrfTokenCache = ''
	return ''
}

function jsonHeaders(): Record<string, string> {
	const csrfToken = getCsrfToken()
	return {
		'Content-Type': 'application/json',
		...(csrfToken ? { 'X-Frappe-CSRF-Token': csrfToken } : {}),
	}
}

/**
 * Create a document via the Frappe REST API.
 */
export async function createDoc<T = Record<string, unknown>>(
	request: APIRequestContext,
	doctype: string,
	doc: Record<string, unknown>,
): Promise<T> {
	const response = await request.post(`/api/resource/${doctype}`, {
		data: doc,
		headers: jsonHeaders(),
	})

	if (!response.ok()) {
		throw new Error(`Failed to create ${doctype}: ${await response.text()}`)
	}

	const result = await response.json()
	return result.data as T
}

/**
 * Get a document by name via the Frappe REST API.
 */
export async function getDoc<T = Record<string, unknown>>(
	request: APIRequestContext,
	doctype: string,
	name: string,
): Promise<T> {
	const response = await request.get(
		`/api/resource/${doctype}/${encodeURIComponent(name)}`,
	)

	if (!response.ok()) {
		throw new Error(
			`Failed to get ${doctype}/${name}: ${await response.text()}`,
		)
	}

	const result = await response.json()
	return result.data as T
}

/**
 * Delete a document via the Frappe REST API.
 */
export async function deleteDoc(
	request: APIRequestContext,
	doctype: string,
	name: string,
): Promise<void> {
	const response = await request.delete(
		`/api/resource/${doctype}/${encodeURIComponent(name)}`,
		{ headers: jsonHeaders() },
	)

	if (!response.ok()) {
		throw new Error(
			`Failed to delete ${doctype}/${name}: ${await response.text()}`,
		)
	}
}

/**
 * Call a Frappe whitelisted method.
 */
export async function callMethod<T = unknown>(
	request: APIRequestContext,
	method: string,
	args: Record<string, unknown> = {},
): Promise<T> {
	const response = await request.post(`/api/method/${method}`, {
		data: args,
		headers: jsonHeaders(),
	})

	if (!response.ok()) {
		throw new Error(`Failed to call ${method}: ${await response.text()}`)
	}

	const result: FrappeResponse<T> = await response.json()
	return result.message as T
}

/**
 * Get a list of documents via the Frappe REST API.
 */
export async function getList<T = Record<string, unknown>>(
	request: APIRequestContext,
	doctype: string,
	options: {
		fields?: string[]
		filters?: Record<string, unknown>
		limit?: number
		orderBy?: string
	} = {},
): Promise<T[]> {
	const params = new URLSearchParams()

	if (options.fields) params.set('fields', JSON.stringify(options.fields))
	if (options.filters) params.set('filters', JSON.stringify(options.filters))
	if (options.limit) params.set('limit_page_length', options.limit.toString())
	if (options.orderBy) params.set('order_by', options.orderBy)

	const response = await request.get(
		`/api/resource/${doctype}?${params.toString()}`,
	)

	if (!response.ok()) {
		throw new Error(
			`Failed to get list of ${doctype}: ${await response.text()}`,
		)
	}

	const result = await response.json()
	return result.data as T[]
}
