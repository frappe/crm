/**
 * Standalone capture script for the CareverseHIMS Self Opt-In portal user guide.
 *
 * Drives the full guest journey end-to-end against cr-dev, pulling the real OTP
 * from the Email Queue between steps, and captures a screenshot at every step.
 * Also demonstrates the email <-> SMS delivery-channel switch.
 *
 * Run:  node e2e/capture_optin_guide.mjs
 * Out:  e2e/proof/guide/*.png
 */
import { chromium } from 'playwright'
import { execSync } from 'node:child_process'
import { mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const BASE = 'https://cr-dev.tiberbu.app'
const URL = `${BASE}/opt-in?network=chak-cbsl`
const OUT = join(__dirname, 'proof/guide')
const BENCH_CWD = '/home/ubuntu/frappe-bench'
const SITE = 'cr-dev.tiberbu.app'

// Pre-qualified contact seeded on cr-dev for network chak-cbsl
const EMAIL = 'dsmwaura@gmail.com'

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

mkdirSync(OUT, { recursive: true })

function fetchNewestEmails(n) {
  const kw = `{'doctype':'Email Queue','fields':['message','creation'],'order_by':'creation desc','limit_page_length':${n}}`
  const cmd = `bench --site ${SITE} execute frappe.client.get_list --kwargs "${kw}"`
  const out = execSync(cmd, { cwd: BENCH_CWD, encoding: 'utf8', maxBuffer: 40 * 1024 * 1024 })
  const s = out.indexOf('[')
  const e = out.lastIndexOf(']')
  if (s === -1 || e === -1) return []
  try {
    return JSON.parse(out.slice(s, e + 1))
  } catch {
    return []
  }
}

function codeFrom(message) {
  const msg = (message || '').replace(/=\r?\n/g, '')
  const m = msg.match(/code is:?\s*(?:<strong>)?\s*(\d{6})/i)
  return m ? m[1] : null
}

function newestCreation() {
  const rows = fetchNewestEmails(1)
  return rows[0]?.creation || ''
}

// Poll for the first OTP email created strictly after `since`.
async function getOtpAfter(since) {
  for (let i = 0; i < 15; i++) {
    const rows = fetchNewestEmails(6)
    for (const r of rows) {
      if (since && r.creation <= since) continue
      const code = codeFrom(r.message)
      if (code) return { code, creation: r.creation }
    }
    await sleep(2000)
  }
  throw new Error('OTP email not found after polling')
}

async function shot(page, name) {
  // Sanitise the caller-supplied label before it reaches the filesystem path:
  // strip everything but [a-z0-9_-] so no '/' or '..' segment can escape OUT.
  const safe = String(name).replace(/[^a-z0-9_-]/gi, '_')
  await sleep(400)
  await page.screenshot({ path: `${OUT}/${safe}.png`, fullPage: true })
  console.log(`  ✓ ${safe}.png`)
}

async function main() {
  const browser = await chromium.launch()

  // ---- Desktop landing ----
  const deskCtx = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    ignoreHTTPSErrors: true,
    deviceScaleFactor: 2,
  })
  const desk = await deskCtx.newPage()
  await desk.goto(URL, { waitUntil: 'networkidle' })
  await desk.getByText('Get Started').waitFor({ timeout: 20000 })
  await shot(desk, '01_landing_desktop')
  await deskCtx.close()

  // ---- Mobile journey ----
  const ctx = await browser.newContext({
    viewport: { width: 414, height: 896 },
    ignoreHTTPSErrors: true,
    deviceScaleFactor: 2,
  })
  const page = await ctx.newPage()
  page.on('console', (m) => {
    if (m.type() === 'error') console.log('  [console.error]', m.text())
  })

  console.log('Step 0: Landing')
  await page.goto(URL, { waitUntil: 'networkidle' })
  await page.getByText('Get Started').waitFor({ timeout: 20000 })
  await shot(page, '02_landing_mobile')

  console.log('Step 1: Contact form + channel selector')
  await page.getByText('Get Started').click()
  await page.getByText('Your Details').waitFor({ timeout: 15000 })
  await page.locator('input[type="text"]').first().fill('Jane')
  await page.locator('input[type="text"]').nth(1).fill('Wanjiku')
  await page.locator('input[type="email"]').fill(EMAIL)
  await page.locator('input[type="tel"]').fill('0722 810 063')
  await page.locator('input[type="text"]').nth(2).fill('Kenyatta National Hospital')
  await page.locator('input[type="text"]').nth(3).fill('Chief Executive Officer')
  await shot(page, '03_contact_email_channel') // Email selected (default)

  // Demonstrate SMS selection on the contact step
  await page.getByRole('button', { name: 'SMS' }).click()
  await shot(page, '04_contact_sms_channel')
  // Revert to Email for the first send (SMS falls back to email on this env anyway)
  await page.getByRole('button', { name: 'Email' }).click()

  console.log('Step 1b: request OTP (email)')
  const since0 = newestCreation()
  await page.getByRole('button', { name: 'Continue' }).click()
  await page.getByText('Verify your identity').waitFor({ timeout: 15000 })
  await shot(page, '05_otp_gate_email')

  // Ensure send #1 landed before switching channel
  const send1 = await getOtpAfter(since0)
  console.log('  send#1 OTP:', send1.code, '@', send1.creation)

  console.log('Step 1c: switch channel to SMS (resend)')
  await page.getByRole('button', { name: /Send the code by SMS instead/i }).click()
  await page.getByText('registered mobile number').waitFor({ timeout: 10000 })
  await shot(page, '06_otp_gate_sms')

  const send2 = await getOtpAfter(send1.creation)
  console.log('  send#2 OTP:', send2.code, '@', send2.creation)

  console.log('Step 1d: enter OTP + verify')
  const otpInputs = page.locator('input[inputmode="numeric"]')
  for (let i = 0; i < 6; i++) await otpInputs.nth(i).fill(send2.code[i])
  await shot(page, '07_otp_filled')
  await page.getByRole('button', { name: 'Verify Code' }).click()

  console.log('Step 2: Facilities')
  await page.getByText('Your Facilities').waitFor({ timeout: 15000 })
  await page.getByText('Select All').click()
  await shot(page, '08_facilities')
  await page.getByRole('button', { name: /Continue \(\d+ selected\)/ }).click()

  console.log('Step 3: Pricing')
  await page.getByText('Your Package Pricing').waitFor({ timeout: 15000 })
  await page.getByText('Grand Total', { exact: false }).first().waitFor({ timeout: 15000 })
  await shot(page, '09_pricing')
  await page.getByRole('button', { name: 'Continue', exact: true }).click()

  console.log('Step 4: Review')
  await page.getByText('Review Your Details').waitFor({ timeout: 15000 })
  await shot(page, '10_review')
  await page.getByRole('button', { name: /Continue to Terms/ }).click()

  console.log('Step 5: Terms')
  await page.getByText('Terms & Conditions').first().waitFor({ timeout: 15000 })
  await sleep(1500) // let T&C html render
  await page.evaluate(() => {
    const el = document.querySelector('[class*="max-h-"]')
    if (el) {
      el.scrollTop = el.scrollHeight
      el.dispatchEvent(new Event('scroll'))
    }
  })
  await sleep(500)
  await page.locator('input[type="checkbox"]').check()
  await shot(page, '11_terms')
  await page.getByRole('button', { name: 'Continue', exact: true }).click()

  console.log('Step 6: Commit')
  await page.getByText('Ready to Commit?').waitFor({ timeout: 15000 })
  await shot(page, '12_commit')
  await page.getByRole('button', { name: /Commit & Opt In/ }).click()

  console.log('Step 7: Progress')
  await page.getByText('Setting things up...').waitFor({ timeout: 10000 }).catch(() => {})
  await shot(page, '13_progress')

  console.log('Step 8: Success (waiting for background pipeline)...')
  await page.getByText("You're in!").waitFor({ timeout: 120000 })
  await sleep(800)
  await shot(page, '14_success')

  // Capture the reference number shown on success
  const refText = await page.textContent('body')
  const refMatch = refText.match(/OIS-\d{4}-\d+/)
  console.log('  Submission reference:', refMatch ? refMatch[0] : '(not found on page)')

  await browser.close()
  console.log('DONE. Screenshots in', OUT)
  if (refMatch) console.log('SUBMISSION_REF=' + refMatch[0])
}

main().catch((e) => {
  console.error('CAPTURE FAILED:', e.message)
  process.exit(1)
})
