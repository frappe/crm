import { test, expect } from '@playwright/test'
import { LoginPage } from '../pages'

/**
 * Exercises the real login flow through Frappe's login page into the CRM SPA.
 * Runs without the shared auth state so it can assert the guest -> logged-in
 * transition itself.
 */
test.describe('Login', () => {
	test.use({ storageState: { cookies: [], origins: [] } })

	test('logs in and lands on the CRM app', async ({ page }) => {
		const login = new LoginPage(page)
		await login.login(
			process.env.FRAPPE_USER || 'Administrator',
			process.env.FRAPPE_PASSWORD || 'admin',
		)

		await expect(page).toHaveURL(/\/crm/)
		// The CRM SPA has booted into its mount point.
		await expect(page.locator('#app')).not.toBeEmpty()
	})

	test('rejects invalid credentials', async ({ page }) => {
		const login = new LoginPage(page)
		await login.goto()
		await page.fill('#login_email', 'Administrator')
		await page.fill('#login_password', 'wrong-password')
		await page.locator('#login_password').press('Enter')

		await login.expectOnLoginPage()
	})
})
