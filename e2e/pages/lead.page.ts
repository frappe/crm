import { Page, expect } from '@playwright/test'

/**
 * Lead detail view (/crm/leads/:name): convert-to-deal and email compose.
 */
export class LeadPage {
	constructor(private page: Page) {}

	async goto(name: string) {
		await this.page.goto(`/crm/leads/${name}`)
		await this.page.waitForLoadState('networkidle')
	}

	/** Open the Convert-to-Deal modal and confirm; resolves on the new deal page. */
	async convertToDeal() {
		await this.page
			.getByRole('button', { name: 'Convert to Deal' })
			.click()
		const dialog = this.page.getByRole('dialog')
		await expect(
			dialog.getByRole('heading', { name: 'Convert to Deal' }),
		).toBeVisible()
		await dialog.getByRole('button', { name: 'Convert', exact: true }).click()
		// Conversion redirects to the created deal.
		await this.page.waitForURL(/\/crm\/deals\//, { timeout: 30000 })
	}

	/** Toggle the email composer open. */
	async openEmailBox() {
		await this.page.getByRole('button', { name: 'Reply' }).click()
	}

	/** Type a body into the composer and send. Subject is pre-filled by CRM. */
	async sendEmail(body: string) {
		const editor = this.page.locator('[contenteditable="true"]').last()
		await editor.click()
		await editor.fill(body)
		await this.page.getByRole('button', { name: 'Send', exact: true }).click()
	}

	/** Switch to a named tab in the activity area (Activity, Emails, ...). */
	async openTab(name: string) {
		await this.page.getByRole('tab', { name }).click()
	}
}
