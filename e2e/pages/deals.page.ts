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
	 * Submit the deal. "Primary email" identifies it later. Value and closure
	 * date are only mandatory when a site customizes them (Property Setter), so
	 * they are filled conditionally to stay portable across sites.
	 */
	async createDeal(email: string) {
		const dialog = this.page.getByRole('dialog')
		await dialog.getByPlaceholder('Primary email', { exact: true }).fill(email)
		await this.fillIfPresent(dialog, 'Expected Deal Value', '1000')
		await this.fillIfPresent(dialog, 'Expected Closure Date', '2026-12-31', true)

		await dialog.getByRole('button', { name: 'Create', exact: true }).click()
		await expect(
			this.page.getByRole('heading', { name: 'Create Deal' }),
		).toBeHidden()
	}

	private async fillIfPresent(
		scope: ReturnType<Page['getByRole']>,
		placeholder: string,
		value: string,
		isDate = false,
	) {
		const field = scope.getByPlaceholder(placeholder, { exact: true })
		if (!(await field.count())) return
		await field.fill(value)
		if (isDate) await field.press('Enter')
	}
}
