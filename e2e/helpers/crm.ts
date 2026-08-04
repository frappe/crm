import { APIRequestContext } from '@playwright/test'
import { createDoc, deleteDoc, getList } from './frappe'

export const LEAD_DOCTYPE = 'CRM Lead'
export const DEAL_DOCTYPE = 'CRM Deal'

export interface LeadData {
	first_name: string
	last_name?: string
	email?: string
	organization?: string
	mobile_no?: string
}

/**
 * Generate a unique suffix so parallel/repeat runs don't collide.
 */
export function uniqueSuffix(): string {
	return `${Date.now()}-${Math.floor(Math.random() * 1000)}`
}

/**
 * Build a lead payload with unique, valid test data.
 */
export function buildLead(overrides: Partial<LeadData> = {}): LeadData {
	const id = uniqueSuffix()
	return {
		first_name: `E2E Lead ${id}`,
		email: `e2e-lead-${id}@example.com`,
		organization: `E2E Org ${id}`,
		mobile_no: '9999999999',
		...overrides,
	}
}

/**
 * Seed a lead via the API (used by tests that start from an existing lead).
 */
export async function seedLead(
	request: APIRequestContext,
	overrides: Partial<LeadData> = {},
): Promise<{ name: string } & LeadData> {
	const data = buildLead(overrides)
	const doc = await createDoc<{ name: string }>(request, LEAD_DOCTYPE, data)
	return { ...data, name: doc.name }
}

/**
 * Delete every lead/deal created by E2E runs (matched by the e2e-* email).
 */
export async function cleanupE2ERecords(
	request: APIRequestContext,
): Promise<void> {
	for (const doctype of [LEAD_DOCTYPE, DEAL_DOCTYPE]) {
		const rows = await getList<{ name: string }>(request, doctype, {
			fields: ['name'],
			filters: { email: ['like', 'e2e-%@example.com'] },
			limit: 500,
		})
		for (const row of rows) {
			try {
				await deleteDoc(request, doctype, row.name)
			} catch {
				// best-effort cleanup; ignore already-deleted / linked rows
			}
		}
	}
}
