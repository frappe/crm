import { Page, expect } from '@playwright/test'

/**
 * Deals list view (/crm/deals) and the "Create Deal" modal.
 */
export class DealsPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/crm/deals')
		await this.page.waitForLoadState('networkidle')
	}

	async openCreateModal() {
		await this.page.getByRole('button', { name: 'Create', exact: true }).click()
		await expect(
			this.page.getByRole('heading', { name: 'Create Deal' }),
		).toBeVisible()
	}

	/**
	 * Submit the deal. The Create Deal modal's fields are mostly Link/Select
	 * with sensible defaults, so an email is enough to identify it later.
	 */
	async createDeal(email: string) {
		const dialog = this.page.getByRole('dialog')
		const emailInput = dialog.getByPlaceholder('Enter Email')
		if (await emailInput.count()) await emailInput.fill(email)

		await dialog.getByRole('button', { name: 'Create', exact: true }).click()
		await expect(
			this.page.getByRole('heading', { name: 'Create Deal' }),
		).toBeHidden()
	}
}
