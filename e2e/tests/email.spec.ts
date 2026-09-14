import { test, expect } from '@playwright/test'
import { LeadPage } from '../pages'
import { cleanupE2ERecords, getList, seedLead } from '../helpers'

test.describe('Send email from lead view', () => {
	test.afterAll(async ({ request }) => {
		await cleanupE2ERecords(request)
	})

	test('composes and sends an email that is recorded as a Communication', async ({
		page,
		request,
	}) => {
		const lead = await seedLead(request)
		const body = `E2E email body ${Date.now()}`
		const leadPage = new LeadPage(page)

		await leadPage.goto(lead.name)
		await leadPage.clearComposerDraft()
		await leadPage.openEmailBox()
		await leadPage.sendEmail(body)

		// The send creates a Communication linked to the lead (no SMTP delivery needed).
		await expect
			.poll(async () => {
				const rows = await getList(request, 'Communication', {
					filters: {
						reference_doctype: 'CRM Lead',
						reference_name: lead.name,
						communication_type: 'Communication',
					},
					fields: ['name'],
				})
				return rows.length
			})
			.toBeGreaterThan(0)

		// And it surfaces in the lead's Emails tab. With a cleared draft the
		// recipient row reflects this lead's email and renders outside the
		// sandboxed body iframe, so it is reliable to assert on.
		await leadPage.openTab('Emails')
		await expect(page.getByText(lead.email!).first()).toBeVisible()
	})
})
