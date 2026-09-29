import { test, expect, Page, Request } from '@playwright/test'
import { LeadsPage } from '../pages'
import { cleanupE2ERecords, seedLead } from '../helpers'

const DEFAULT_PAGE_LENGTH = 20
const GET_DATA = 'crm.api.doc.get_data'

interface GetDataPayload {
	page_length: number | null
}

interface GetDataResponse {
	message: { row_count: number; total_count: number; page_length: number }
}

/** The next list fetch, as the JSON body the client sent and the message the server returned. */
async function nextListFetch(page: Page, trigger: () => Promise<void>) {
	const requestPromise = page.waitForRequest(
		(req: Request) => req.url().includes(GET_DATA) && req.method() === 'POST',
	)
	await trigger()
	const request = await requestPromise
	const response = await request.response()
	return {
		payload: request.postDataJSON() as GetDataPayload,
		status: response?.status(),
		message: ((await response?.json()) as GetDataResponse | undefined)?.message,
	}
}

test.describe('List view pagination', () => {
	test.beforeAll(async ({ request }) => {
		// One more than the default page size so "Load More" is rendered.
		for (let i = 0; i <= DEFAULT_PAGE_LENGTH; i++) {
			await seedLead(request)
		}
	})

	test.afterAll(async ({ request }) => {
		await cleanupE2ERecords(request)
	})

	test('"Load More" requests the next page instead of re-fetching the first (#2835)', async ({
		page,
	}) => {
		const leads = new LeadsPage(page)

		// A cold load has no previous response to read the page size from, so
		// the client must send the default itself rather than omit the key.
		const initial = await nextListFetch(page, () => leads.goto())
		expect(initial.payload.page_length).toBe(DEFAULT_PAGE_LENGTH)
		expect(initial.status).toBe(200)
		expect(initial.message?.row_count).toBe(DEFAULT_PAGE_LENGTH)

		const loadMore = page.getByRole('button', { name: 'Load More', exact: true })
		await expect(loadMore).toBeVisible()

		// Before the fix the client sent page_length: null (undefined + undefined),
		// which the server rejected with a FrappeTypeError.
		const next = await nextListFetch(page, () => loadMore.click())
		expect(next.payload.page_length).toBe(DEFAULT_PAGE_LENGTH * 2)
		expect(next.status).toBe(200)
		expect(next.message?.row_count).toBeGreaterThan(DEFAULT_PAGE_LENGTH)
		expect(next.message?.row_count).toBe(
			Math.min(DEFAULT_PAGE_LENGTH * 2, next.message?.total_count ?? 0),
		)
	})
})
