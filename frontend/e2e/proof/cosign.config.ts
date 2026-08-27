import { defineConfig, devices } from '@playwright/test'

// Standalone proof config — single project, NO setup dependency, targets cr-dev.
export default defineConfig({
	testDir: '.',
	fullyParallel: false,
	workers: 1,
	timeout: 180000,
	reporter: [['list']],
	expect: { timeout: 15000 },
	use: {
		baseURL: process.env.BASE_URL || 'https://cr-dev.tiberbu.app',
		ignoreHTTPSErrors: true,
		actionTimeout: 20000,
		navigationTimeout: 45000,
		viewport: { width: 1440, height: 1600 },
	},
	projects: [
		{ name: 'proof', use: { ...devices['Desktop Chrome'] } },
	],
})
