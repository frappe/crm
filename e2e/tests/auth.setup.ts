import * as fs from 'fs'
import * as path from 'path'
import { expect, test as setup } from '@playwright/test'

const authFile = 'e2e/.auth/user.json'
const csrfFile = 'e2e/.auth/csrf.json'

/**
 * Authentication setup - runs once before all tests.
 * Logs in via the Frappe API, captures the CSRF token, and saves storage state.
 */
setup('authenticate', async ({ page }) => {
	const authDir = path.dirname(authFile)
	if (!fs.existsSync(authDir)) {
		fs.mkdirSync(authDir, { recursive: true })
	}

	const loginResponse = await page.request.post('/api/method/login', {
		form: {
			usr: process.env.FRAPPE_USER || 'Administrator',
			pwd: process.env.FRAPPE_PASSWORD || 'admin',
		},
	})
	expect(loginResponse.ok()).toBeTruthy()

	const userResponse = await page.request.get(
		'/api/method/frappe.auth.get_logged_user',
	)
	expect(userResponse.ok()).toBeTruthy()
	const userData = await userResponse.json()
	expect(userData.message).not.toBe('Guest')
	console.log(`Authenticated as: ${userData.message}`)

	// Load the CRM app so window.frappe.csrf_token is available.
	await page.goto('/crm')
	await page.waitForLoadState('networkidle')

	// The CRM SPA injects boot keys onto window (see crm/www/crm.html),
	// so the token lives at window.csrf_token.
	const csrfToken = await page.evaluate(() => {
		const w = window as unknown as {
			csrf_token?: string
			frappe?: { csrf_token?: string }
		}
		return w.csrf_token || w.frappe?.csrf_token
	})

	if (csrfToken) {
		fs.writeFileSync(csrfFile, JSON.stringify({ csrf_token: csrfToken }))
	}

	await page.context().storageState({ path: authFile })
})
