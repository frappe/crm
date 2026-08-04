import { APIRequestContext, Page } from '@playwright/test'

/**
 * Login via the Frappe API (faster than UI login).
 * Sets session cookies on the request context for subsequent API calls.
 */
export async function loginViaAPI(
	request: APIRequestContext,
	email = 'Administrator',
	password = 'admin',
): Promise<void> {
	const response = await request.post('/api/method/login', {
		form: { usr: email, pwd: password },
	})

	if (!response.ok()) {
		throw new Error(
			`Login failed: ${response.status()} ${await response.text()}`,
		)
	}
}

/**
 * Logout the current user.
 */
export async function logout(page: Page): Promise<void> {
	await page.goto('/api/method/logout')
	await page.waitForLoadState('networkidle')
}

/**
 * Check if a user is logged in by verifying the session.
 */
export async function isLoggedIn(request: APIRequestContext): Promise<boolean> {
	try {
		const response = await request.get(
			'/api/method/frappe.auth.get_logged_user',
		)
		if (!response.ok()) return false

		const data = await response.json()
		return data.message && data.message !== 'Guest'
	} catch {
		return false
	}
}
