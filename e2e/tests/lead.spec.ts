import { test, expect } from '@playwright/test'
import { LeadsPage } from '../pages'
import { buildLead, cleanupE2ERecords, getList, LEAD_DOCTYPE } from '../helpers'

test.describe('Lead creation', () => {
	test.afterAll(async ({ request }) => {
		await cleanupE2ERecords(request)
	})

	test('creates a lead from the leads list view', async ({ page, request }) => {
		const lead = buildLead()
		const leads = new LeadsPage(page)

		await leads.goto()
		await leads.openCreateModal()
		await leads.createLead(lead)

		// The new lead is persisted and queryable via the API.
		await expect
			.poll(async () => {
				const rows = await getList(request, LEAD_DOCTYPE, {
					filters: { email: lead.email },
					fields: ['name'],
				})
				return rows.length
			})
			.toBeGreaterThan(0)
	})
})
