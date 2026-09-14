import { defineConfig, devices } from '@playwright/test'

// Auth state file path (gitignored)
const authFile = 'e2e/.auth/user.json'

/**
 * Playwright configuration for Frappe CRM E2E tests.
 *
 * Uses the "setup project" pattern for authentication:
 * 1. The setup project logs in once and saves the storage state to a file.
 * 2. The chromium project depends on setup and reuses the stored state.
 *
 * @see https://playwright.dev/docs/auth
 */
export default defineConfig({
	testDir: './e2e/tests',
	fullyParallel: false, // sequential for Frappe state consistency
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
	workers: 1, // single worker for Frappe session management
	reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'html',
	timeout: 60000,

	expect: {
		timeout: 10000,
	},

	use: {
		baseURL: process.env.BASE_URL || 'http://crm.test:8000',
		trace: 'on-first-retry',
		video: 'retain-on-failure',
		screenshot: 'only-on-failure',
		actionTimeout: 15000,
		navigationTimeout: 30000,
	},

	projects: [
		{
			name: 'setup',
			testMatch: /auth\.setup\.ts/,
		},
		{
			name: 'chromium',
			use: {
				...devices['Desktop Chrome'],
				storageState: authFile,
			},
			dependencies: ['setup'],
		},
	],
})
