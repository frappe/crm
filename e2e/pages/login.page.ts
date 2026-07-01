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
		await this.waitForLoggedIn()
	}

	/**
	 * Detect login success robustly. Frappe may navigate away from /login or
	 * complete auth in place, so race three independent signals: the URL
	 * leaving /login, the CRM SPA mounting, or the session becoming
	 * authenticated. Then ensure we actually land in the CRM app.
	 */
	private async waitForLoggedIn() {
		await Promise.race([
			// Full navigation away from the login page. A plain /crm match would
			// pass immediately because the URL carries redirect-to=/crm.
			this.page.waitForURL((url) => !url.pathname.startsWith('/login'), {
				timeout: 30000,
			}),
			// In-place auth: the CRM SPA mounts into #app.
			this.page
				.locator('#app > *')
				.first()
				.waitFor({ state: 'attached', timeout: 30000 }),
			// Server-side signal: the session is authenticated. page.request
			// shares the browser context cookies set by the login POST.
			expect
				.poll(
					async () => {
						const res = await this.page.request.get(
							'/api/method/frappe.auth.get_logged_user',
						)
						return res.ok() ? (await res.json()).message : 'Guest'
					},
					{ timeout: 30000 },
				)
				.not.toBe('Guest'),
		])

		// The session is established; make sure we're on the CRM app even if the
		// post-login redirect hasn't fired yet.
		if (new URL(this.page.url()).pathname.startsWith('/login')) {
			await this.page.goto('/crm')
			await this.page.waitForLoadState('networkidle')
		}
	}

	async expectOnLoginPage() {
		await expect(this.page).toHaveURL(/.*login.*/)
	}
}
