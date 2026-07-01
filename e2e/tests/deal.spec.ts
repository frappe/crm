import { test, expect } from '@playwright/test'
import { DealsPage } from '../pages'
import {
	cleanupE2ERecords,
	DEAL_DOCTYPE,
	getList,
	uniqueSuffix,
} from '../helpers'

test.describe('Deal creation', () => {
	test.afterAll(async ({ request }) => {
		await cleanupE2ERecords(request)
	})

	test('creates a deal from the deals list view', async ({ page, request }) => {
		const email = `e2e-deal-${uniqueSuffix()}@example.com`
		const deals = new DealsPage(page)

		await deals.goto()
		await deals.openCreateModal()
		await deals.createDeal(email)

		await expect
			.poll(async () => {
				const rows = await getList(request, DEAL_DOCTYPE, {
					filters: { email },
					fields: ['name'],
				})
				return rows.length
			})
			.toBeGreaterThan(0)
	})
})
