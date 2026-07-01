import { test, expect } from '@playwright/test'
import { LeadPage } from '../pages'
import { cleanupE2ERecords, DEAL_DOCTYPE, getList, seedLead } from '../helpers'

test.describe('Lead to deal conversion', () => {
	test.afterAll(async ({ request }) => {
		await cleanupE2ERecords(request)
	})

	test('converts an existing lead into a deal', async ({ page, request }) => {
		const lead = await seedLead(request)
		const leadPage = new LeadPage(page)

		await leadPage.goto(lead.name)
		await leadPage.convertToDeal()

		// A deal now carries the converted lead's email.
		await expect
			.poll(async () => {
				const rows = await getList(request, DEAL_DOCTYPE, {
					filters: { email: lead.email },
					fields: ['name'],
				})
				return rows.length
			})
			.toBeGreaterThan(0)
	})
})
