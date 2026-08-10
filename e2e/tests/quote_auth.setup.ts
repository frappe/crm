/**
 * Auth setup for cr-dev.tiberbu.app.
 * Uses JSON body (not form encoding) because the site uses a custom login page.
 */
import * as fs from 'fs'
import * as path from 'path'
import { expect, test as setup } from '@playwright/test'

const authFile = 'e2e/.auth/quote-user.json'
const csrfFile = 'e2e/.auth/csrf.json'

setup('authenticate for quote tests', async ({ page }) => {
	const authDir = path.dirname(authFile)
	if (!fs.existsSync(authDir)) {
		fs.mkdirSync(authDir, { recursive: true })
	}

	const user = process.env.FRAPPE_USER || 'Administrator'
	const pwd  = process.env.FRAPPE_PASSWORD || 'admin123'

	// JSON body login (custom login page pattern on this site)
	const loginResponse = await page.request.post('/api/method/login', {
		data: { usr: user, pwd },
		headers: { 'Content-Type': 'application/json' },
	})
	expect(loginResponse.ok(), `Login failed: ${loginResponse.status()}`).toBeTruthy()
	const loginBody = await loginResponse.json()
	expect(loginBody.message).toBe('Logged In')

	// Load the CRM SPA to capture the CSRF token
	await page.goto('/crm')
	await page.waitForLoadState('networkidle')

	const csrfToken = await page.evaluate(() => {
		const w = window as unknown as { csrf_token?: string; frappe?: { csrf_token?: string } }
		return w.csrf_token || w.frappe?.csrf_token || ''
	})

	if (csrfToken) {
		fs.writeFileSync(csrfFile, JSON.stringify({ csrf_token: csrfToken }))
	}

	await page.context().storageState({ path: authFile })
	console.log(`Authenticated as ${user}, CSRF token captured: ${!!csrfToken}`)
})
