import { test, expect } from '@playwright/test'
import { cleanupE2ERecords, seedLead } from '../helpers'

test.describe('Link control', () => {
	test.afterAll(async ({ request }) => {
		await cleanupE2ERecords(request)
	})

	test('says it is loading until the search answers', async ({
		page,
		request,
	}) => {
		const lead = await seedLead(request)

		let answerSearch = () => {}
		const answered = new Promise<void>((resolve) => (answerSearch = resolve))
		await page.route(
			/frappe\.desk\.search\.search_link.*CRM(\+|%20)Lost(\+|%20)Reason/,
			async (route) => {
				await answered
				await route.continue()
			},
		)

		await page.goto(`/crm/leads/${lead.name}`)
		await page.waitForLoadState('networkidle')
		// the lead's status comes before the "New" menu of the activity tab
		await page.getByRole('button', { name: 'New', exact: true }).first().click()
		await page.getByRole('menuitem', { name: 'Junk' }).click()

		const dialog = page.getByRole('dialog').filter({ hasText: 'Lost Reason' })
		await dialog.locator('button[id]').click()
		await expect(page.getByText('Loading...')).toBeVisible()
		await expect(page.getByText('No results found')).toBeHidden()

		answerSearch()
		await expect(page.getByRole('option').first()).toBeVisible()
		await expect(page.getByText('Loading...')).toBeHidden()

		await page.getByPlaceholder('Search').fill('no reason has this name')
		await expect(page.getByText('No results found')).toBeVisible()
	})
})
