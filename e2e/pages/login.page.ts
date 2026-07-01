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
		await this.page.fill('#login_email', email)
		await this.page.fill('#login_password', password)
		// Submit via Enter to avoid coupling to the button label/class, which
		// varies across Frappe versions.
		await this.page.locator('#login_password').press('Enter')
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
