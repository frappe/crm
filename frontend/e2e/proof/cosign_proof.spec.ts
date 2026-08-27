import { execSync } from 'child_process'
import { writeFileSync } from 'fs'
import { expect, test } from '@playwright/test'

const SHOTS = '/tmp/cosign-qa'
const OPTIN_EMAIL = 'salim@tiberbu.com'
const NETWORK = 'apex-medical'
const MGR_USER = 'sales-manager@tiberbu.test'
const MGR_PWD = 'QaProof!2026'
const DEAL = '71189'
const KNOWN_OTP = '123456'

// Seed a known OTP hash onto every active membership for the opt-in email so the
// UI OTP gate passes deterministically (the real code is dispatched async and
// stored only as an HMAC hash — unreadable, hence the seed).
function seedOtp() {
	const py = [
		'import frappe',
		'from crm.api.optin import _hmac_hex, _get_signing_key',
		'import frappe.utils',
		'h = _hmac_hex(_get_signing_key(), "123456")',
		'exp = frappe.utils.add_to_date(frappe.utils.now_datetime(), minutes=10)',
		'rows = frappe.get_list("CRM Facility Membership", filters={"contact_email":"salim@tiberbu.com","network":"apex-medical","status":"Active"}, pluck="name", ignore_permissions=True)',
		'for n in rows:',
		'    d = frappe.get_doc("CRM Facility Membership", n)',
		'    d.otp_hash = h',
		'    d.otp_expiry = exp',
		'    d.otp_attempts = 0',
		'    d.save(ignore_permissions=True)',
		'frappe.db.commit()',
		'print("OTP_SEEDED", len(rows))',
	].join('\n')
	const cmd = `printf '%s\\n' '${py}' 'exit' | bench --site cr-dev.tiberbu.app console 2>&1 | grep OTP_SEEDED`
	const out = execSync(cmd, { cwd: '/home/ubuntu/frappe-bench', encoding: 'utf-8', timeout: 120000 })
	console.log('seedOtp ->', out.trim())
}

// ── SURFACE 2: Deal Contracting tab — auto-populated co-signatories ──────────
test('Surface 2: Contracting tab co-signatories (light + dark)', async ({ browser }) => {
	for (const scheme of ['light', 'dark'] as const) {
		const ctx = await browser.newContext({ colorScheme: scheme })
		const page = await ctx.newPage()

		// CRM uses [data-theme] driven by localStorage 'theme'
		await page.addInitScript((s) => {
			try { window.localStorage.setItem('theme', s) } catch {}
		}, scheme)

		const login = await page.request.post('/api/method/login', {
			data: { usr: MGR_USER, pwd: MGR_PWD },
			headers: { 'Content-Type': 'application/json' },
		})
		expect(login.ok(), `login failed: ${login.status()}`).toBeTruthy()

		await page.goto(`/crm/deals/${DEAL}`)
		await page.waitForLoadState('networkidle')

		// Must NOT be the login page
		expect(page.url(), 'landed on login page').not.toContain('/login')

		// Dismiss the "Getting started" onboarding popover if present (overlaps content)
		const skip = page.getByText('Skip all', { exact: false })
		if (await skip.count()) { await skip.first().click().catch(() => {}) }

		// Switch to the Quoting tab (last tab; mounts QuotingTab → ContractingPanel)
		const quotingTab = page.getByText('Quoting', { exact: true })
		await quotingTab.first().scrollIntoViewIfNeeded()
		await quotingTab.first().click()
		await page.waitForTimeout(1500)

		// The co-signatory block is the proof anchor
		const anchor = page.getByText('Network & Tiberbu Co-Signatories', { exact: false })
		await anchor.scrollIntoViewIfNeeded()
		await expect(anchor).toBeVisible({ timeout: 20000 })

		await page.waitForTimeout(1200) // let the resource settle + chips render
		await anchor.scrollIntoViewIfNeeded()
		await page.screenshot({ path: `${SHOTS}/surface2-contracting-${scheme}.png`, fullPage: true })
		await ctx.close()
	}
})

// ── SURFACE 3: ContractingPanel inline-edit of a pending signatory row ───────
test('Surface 3: inline-edit pending signatory (nc-s3-3)', async ({ browser }) => {
	const ctx = await browser.newContext({ colorScheme: 'light' })
	const page = await ctx.newPage()

	const login = await page.request.post('/api/method/login', {
		data: { usr: MGR_USER, pwd: MGR_PWD },
		headers: { 'Content-Type': 'application/json' },
	})
	expect(login.ok(), `login failed: ${login.status()}`).toBeTruthy()

	await page.goto(`/crm/deals/${DEAL}`)
	await page.waitForLoadState('networkidle')

	const quotingTab = page.getByText('Quoting', { exact: true })
	await quotingTab.first().scrollIntoViewIfNeeded()
	await quotingTab.first().click()
	await page.waitForTimeout(1500)

	// The "Signatories" block only renders when a contract exists
	const sigHeading = page.getByText('Signatories', { exact: true }).first()
	await expect(sigHeading).toBeVisible({ timeout: 20000 })
	await sigHeading.scrollIntoViewIfNeeded()

	// Click the first pending-row "Edit" to reveal the inline name/email form
	const editBtn = page.getByRole('button', { name: 'Edit', exact: true })
	await editBtn.first().click()
	await page.waitForTimeout(600)

	// Proof anchor: the inline-edit hint copy is unique to the edit form
	await expect(
		page.getByText('invalidates the old link', { exact: false }),
	).toBeVisible({ timeout: 10000 })
	await page.screenshot({ path: `${SHOTS}/surface3-inline-edit.png`, fullPage: true })
	await ctx.close()
})

// Run an inline python snippet through the site's bench console and return stdout.
// The snippet is written to a temp file and exec'd with globals==locals so nested
// scopes (comprehensions) resolve module-level names — no shell escaping games.
function runPy(lines: string[], marker: string): string {
	const path = `/tmp/ncqa_run_${Date.now()}.py`
	writeFileSync(path, lines.join('\n'))
	const cmd = `printf '%s\\nexit\\n' "g={}; exec(open('${path}').read(), g, g)" | bench --site cr-dev.tiberbu.app console 2>&1 | grep '${marker}'`
	return execSync(cmd, { cwd: '/home/ubuntu/frappe-bench', encoding: 'utf-8', timeout: 120000 }).trim()
}

// ── SURFACE 4 (nc-qa): guest signing portal — OTP → read → sign → success ────
test('Surface 4: guest signing portal end-to-end (nc-qa)', async ({ browser }) => {
	// 1. Provision a throwaway contract with a pending, invited Facility Signatory.
	const setup = execSync(
		`printf '%s\\nexit\\n' "g={}; exec(open('/tmp/ncqa_setup.py').read(), g, g)" | bench --site cr-dev.tiberbu.app console 2>&1 | grep 'NCQA|'`,
		{ cwd: '/home/ubuntu/frappe-bench', encoding: 'utf-8', timeout: 120000 },
	)
	const m = setup.match(/NCQA\|contract=(\S+)\|token=(\S+)/)
	expect(m, `setup did not emit contract/token: ${setup}`).toBeTruthy()
	const contract = m![1]
	const token = m![2]
	const role = 'Facility Signatory'
	console.log('nc-qa provisioned', contract, token.slice(0, 8) + '…')

	const ctx = await browser.newContext({ colorScheme: 'light', ignoreHTTPSErrors: true })
	const page = await ctx.newPage()

	try {
		// 2. Open the guest portal link (role must be +-encoded, as the invite email builds it).
		await page.goto(`/sign-contract?contract=${contract}&role=${role.replace(/ /g, '+')}&token=${token}`)

		// 3. OTP gate mounts and auto-requests a FRESH random OTP. Wait for it, THEN
		//    overwrite the row's otp_hash with a known code so we can complete the gate.
		await expect(page.getByText('Verify your identity')).toBeVisible({ timeout: 30000 })
		await page.waitForTimeout(1500) // let onMounted request_otp commit first
		const seed = runPy(
			[
				'import frappe',
				'from crm.api import contracts as C',
				`d = frappe.get_doc("CRM Contract", "${contract}")`,
				`row = C._get_signatory_row(d, "${role}")`,
				'row.otp_hash = C._hmac_hex(C._get_signing_key(), "123456")',
				'row.otp_expiry = frappe.utils.add_to_date(frappe.utils.now_datetime(), minutes=10)',
				'row.otp_used = 0',
				'd.save(ignore_permissions=True)',
				'frappe.db.commit()',
				`frappe.cache().set_value(C._attempts_cache_key("${contract}", "${role}"), 0, expires_in_sec=800)`,
				'print("OTP_SET|ok")',
			],
			'OTP_SET|',
		)
		expect(seed, `otp seed failed: ${seed}`).toContain('OTP_SET|ok')

		// 4. Enter the known code and verify.
		const otpInputs = page.locator('input[inputmode="numeric"]')
		await otpInputs.first().click()
		await page.keyboard.type(KNOWN_OTP, { delay: 60 })
		await page.getByRole('button', { name: 'Verify Code' }).click()

		// 5. Sign screen: read the full contract (scroll the panel to the bottom).
		await expect(page.getByRole('heading', { name: 'Review & Sign' })).toBeVisible({ timeout: 30000 })
		await page.waitForTimeout(1200) // contract HTML fetch + render
		await page.evaluate(() => {
			const scrollables = Array.from(document.querySelectorAll<HTMLElement>('*')).filter((e) => {
				const s = getComputedStyle(e)
				return s.overflowY === 'scroll' && e.scrollHeight > e.clientHeight
			})
			for (const el of scrollables) {
				el.scrollTop = el.scrollHeight
				el.dispatchEvent(new Event('scroll'))
			}
		})

		// 6. Confirm the read-authorisation checkbox (only enabled once scrolled).
		const readConfirm = page.locator('#read-confirm')
		await expect(readConfirm).toBeEnabled({ timeout: 10000 })
		await readConfirm.check()

		// 7. Draw a signature on the canvas.
		const canvas = page.locator('canvas')
		await expect(canvas).toBeVisible()
		const box = await canvas.boundingBox()
		expect(box, 'canvas has no bounding box').toBeTruthy()
		const cx = box!.x + box!.width / 2
		const cy = box!.y + box!.height / 2
		await page.mouse.move(cx - 80, cy)
		await page.mouse.down()
		await page.mouse.move(cx - 40, cy - 30)
		await page.mouse.move(cx, cy + 20)
		await page.mouse.move(cx + 40, cy - 20)
		await page.mouse.move(cx + 80, cy)
		await page.mouse.up()
		await page.waitForTimeout(300)

		// 8. Submit the signature.
		const submit = page.getByRole('button', { name: 'Confirm Signature' })
		await expect(submit).toBeEnabled({ timeout: 10000 })
		await submit.click()

		// 9. Success screen is the proof anchor.
		await expect(page.getByText('Your signature has been recorded.')).toBeVisible({ timeout: 30000 })
		await page.screenshot({ path: `${SHOTS}/surface4-portal-signed.png`, fullPage: true })

		// 10. Verify server-side: the row is Signed with a captured IP + timestamp.
		const verify = runPy(
			[
				'import frappe',
				'from crm.api import contracts as C',
				`d = frappe.get_doc("CRM Contract", "${contract}")`,
				`row = C._get_signatory_row(d, "${role}")`,
				'print("VERIFY|status=%s|signed_at=%s|ip=%s|state=%s" % (row.status, bool(row.signed_at), bool(row.signature_ip), d.workflow_state))',
			],
			'VERIFY|',
		)
		console.log('nc-qa', verify)
		expect(verify, `row not signed: ${verify}`).toContain('status=Signed')
		expect(verify).toContain('signed_at=True')
	} finally {
		await ctx.close()
		// 11. Teardown: delete the throwaway contract.
		try {
			runPy(
				[
					'import frappe',
					`frappe.delete_doc("CRM Contract", "${contract}", force=1, ignore_permissions=True)`,
					'frappe.db.commit()',
					'print("TEARDOWN|done")',
				],
				'TEARDOWN|',
			)
		} catch (e) {
			console.log('teardown warning', String(e))
		}
	}
})

// ── SURFACE 1: Opt-in wizard Review step — Facility Witness capture ──────────
test('Surface 1: opt-in Review witness capture (light + dark)', async ({ browser }) => {
	for (const scheme of ['light', 'dark'] as const) {
		const ctx = await browser.newContext({ colorScheme: scheme })
		const page = await ctx.newPage()

		await page.goto(`/opt-in?network=${NETWORK}`)
		await page.waitForLoadState('networkidle')

		// Landing → Get Started
		await page.getByRole('button', { name: 'Get Started' }).click()

		// Contact step: fill email, continue (requests OTP)
		await page.locator('input[type="email"]').first().fill(OPTIN_EMAIL)
		await page.getByRole('button', { name: 'Continue' }).click()

		// Diagnostic: capture whatever renders after Continue (gate vs block state)
		await page.waitForTimeout(3000)
		await page.screenshot({ path: `${SHOTS}/debug-after-continue-${scheme}.png`, fullPage: true })

		// OTP gate visible → seed a known code, then type it
		await expect(page.getByText('Verify your identity')).toBeVisible({ timeout: 20000 })
		seedOtp()
		const otpInputs = page.locator('input[inputmode="numeric"]')
		await otpInputs.first().click()
		await page.keyboard.type(KNOWN_OTP, { delay: 60 })
		await page.getByRole('button', { name: 'Verify Code' }).click()

		// Facilities step → Select All → Continue
		await expect(page.getByRole('button', { name: /Select All/i })).toBeVisible({ timeout: 20000 })
		await page.getByRole('button', { name: /Select All/i }).click()
		await page.getByRole('button', { name: /Continue \(/i }).click()

		// Pricing step → load then Continue
		await page.waitForTimeout(1500)
		const loadBtn = page.getByRole('button', { name: /Calculate|Load|Get Pricing|Show/i })
		if (await loadBtn.count()) { await loadBtn.first().click().catch(() => {}) }
		await page.waitForTimeout(1500)
		await page.getByRole('button', { name: 'Continue', exact: true }).click()

		// Review step → Facility Witness card is the proof anchor
		const witnessAnchor = page.getByText('Facility Witness', { exact: false })
		await expect(witnessAnchor).toBeVisible({ timeout: 20000 })
		await witnessAnchor.scrollIntoViewIfNeeded()
		await page.screenshot({ path: `${SHOTS}/surface1-review-witness-${scheme}.png`, fullPage: true })

		// Bonus: fill witness, prove Continue enables
		await page.getByPlaceholder('Full legal name').fill('Dr. Grace Wanjiru')
		await page.getByPlaceholder('witness@hospital.or.ke').fill('grace.wanjiru@apex.co.ke')
		await page.waitForTimeout(400)
		await page.screenshot({ path: `${SHOTS}/surface1-review-filled-${scheme}.png`, fullPage: true })
		await ctx.close()
	}
})
