import { test, expect } from '@playwright/test'

/**
 * Verifies CRM's authentication handling.
 *
 * Credentials are exercised by the API login in auth.setup (which the whole
 * suite depends on). Driving Frappe's HTML login form directly is unreliable
 * in headless CI and is Frappe's surface, not CRM's — so here we assert the
 * two outcomes CRM itself owns: an authenticated session reaches the app, and
 * a guest is denied.
 */
test.describe('Login', () => {
	test('an authenticated session reaches the CRM app', async ({ page }) => {
		// Uses the shared authenticated storage state from auth.setup.
		await page.goto('/crm')
		await expect(page).toHaveURL(/\/crm/)
		await expect(page.locator('#app > *').first()).toBeVisible()
	})

	test.describe('as a guest', () => {
		test.use({ storageState: { cookies: [], origins: [] } })

		test('cannot access the CRM app', async ({ page }) => {
			await page.goto('/crm')
			await page.waitForLoadState('networkidle')
			// The SPA never mounts for an unauthenticated user (Frappe returns 403).
			await expect(page.locator('#app > *')).toHaveCount(0)
		})
	})
})
