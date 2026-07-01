import { Page, expect } from '@playwright/test'

/**
 * Frappe's standard login page. After a successful login with
 * redirect-to=/crm the browser lands on the CRM SPA.
 */
export class LoginPage {
	constructor(private page: Page) {}

	async goto() {
		await this.page.goto('/login?redirect-to=/crm')
		await this.page.waitForLoadState('networkidle')
	}

	async login(email = 'Administrator', password = 'admin') {
		await this.goto()
		const emailInput = this.page.locator('#login_email')
		const passwordInput = this.page.locator('#login_password')
		await emailInput.waitFor({ state: 'visible' })
		// Frappe's login.js can reset the fields as it initialises, so keep
		// filling until the email value actually sticks before submitting.
		await expect(async () => {
			await emailInput.fill(email)
			await passwordInput.fill(password)
			await expect(emailInput).toHaveValue(email)
		}).toPass({ timeout: 15000 })
		// btn-login is stable across Frappe versions (button text is not).
		await this.page.locator('button.btn-login[type="submit"]').first().click()
		// Wait until we actually leave the login page — a plain /crm match would
		// pass immediately because the URL carries redirect-to=/crm.
		await this.page.waitForURL((url) => !url.pathname.startsWith('/login'), {
			timeout: 30000,
		})
	}

	async expectOnLoginPage() {
		await expect(this.page).toHaveURL(/.*login.*/)
	}
}
