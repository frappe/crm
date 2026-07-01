import { Locator, Page, expect } from '@playwright/test'
import { LeadData } from '../helpers/crm'

/**
 * Leads list view (/crm/leads) and the "Create Lead" modal.
 *
 * Fields render via FieldLayout: a plain label div plus an input whose
 * placeholder is "Enter {label}" (text) or "Select {label}" (Link/Select).
 * We drive the plain text fields by placeholder for stable selectors.
 */
export class LeadsPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/crm/leads')
		await this.page.waitForLoadState('networkidle')
	}

	async openCreateModal() {
		await this.page.getByRole('button', { name: 'Create', exact: true }).click()
		await expect(
			this.page.getByRole('heading', { name: 'Create Lead' }),
		).toBeVisible()
	}

	/** Fill the mandatory text fields and submit; resolves once the modal closes. */
	async createLead(data: LeadData) {
		const dialog = this.page.getByRole('dialog')
		await dialog.getByPlaceholder('Enter First Name').fill(data.first_name)
		if (data.last_name)
			await dialog.getByPlaceholder('Enter Last Name').fill(data.last_name)
		if (data.email)
			await dialog.getByPlaceholder('Enter Email').fill(data.email)

		await dialog.getByRole('button', { name: 'Create', exact: true }).click()
		await expect(
			this.page.getByRole('heading', { name: 'Create Lead' }),
		).toBeHidden()
	}

	/** A list row matching the given text (e.g. the lead's name/email). */
	row(text: string): Locator {
		return this.page.getByRole('link').filter({ hasText: text }).first()
	}
}
