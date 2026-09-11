// useDocument pulls in stores, composables and a live createDocumentResource
// that aren't wired up for vitest — stub them so this test exercises only the
// save-error toast selection in setValue.onError (regression for #1703).
vi.mock('@/data/script', () => ({
  getScript: () => ({ setupScript: vi.fn(), scripts: {} }),
}))
vi.mock('@/stores/global', () => ({ globalStore: () => ({}) }))
vi.mock('@/stores/meta', () => ({ getMeta: () => ({}) }))
vi.mock('@/composables/useAttachments', () => ({
  useAttachments: () => ({
    trackOldFile: vi.fn(),
    processPendingDeletions: vi.fn(),
  }),
}))
vi.mock('@/composables/settings', () => ({
  showSettings: { value: false },
  activeSettingsPage: { value: '' },
}))
vi.mock('@/utils', () => ({
  runSequentially: vi.fn(),
  parseAssignees: (d) => d,
  sanitizeText: (t) => t,
}))
vi.mock('@/utils/fieldTransforms', () => ({ findMissingMandatory: () => [] }))
vi.mock('@/utils/fetchFrom', () => ({
  getFetchSource: vi.fn(),
  getFieldsToFetch: vi.fn(),
  getPendingFetchFields: vi.fn(),
  getSourceFieldnames: vi.fn(),
}))

const { toast, captured } = vi.hoisted(() => ({
  toast: { error: vi.fn(), success: vi.fn() },
  captured: { options: null },
}))

vi.mock('frappe-ui', () => ({
  call: vi.fn(),
  toast,
  createResource: () => ({}),
  createDocumentResource: (options) => {
    captured.options = options
    return { doc: {}, save: { submit: vi.fn() } }
  },
}))

import { useDocument } from '@/data/document'

describe('useDocument setValue.onError toasts', () => {
  let onError

  // useDocument caches the resource per docname, so set it up once and
  // reuse the captured handler across tests.
  beforeAll(() => {
    useDocument('CRM Lead', 'CRM-LEAD-TEST')
    onError = captured.options.setValue.onError
  })

  beforeEach(() => {
    toast.error.mockClear()
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows one toast per server message', () => {
    onError({ messages: ['Editing this lead is not allowed.'] })

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith(
      'Editing this lead is not allowed.',
    )
  })

  it('shows the generic toast when messages is an empty array', () => {
    onError({ messages: [] })

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith(
      'An error occurred while updating the document',
    )
  })

  it('shows the generic toast when messages is missing', () => {
    onError({})

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith(
      'An error occurred while updating the document',
    )
  })

  it('collapses mandatory errors into a single toast', () => {
    onError({
      exc_type: 'MandatoryError',
      messages: ['Missing: first_name', 'Missing: email'],
    })

    expect(toast.error).toHaveBeenCalledTimes(1)
    expect(toast.error).toHaveBeenCalledWith(
      'Mandatory field error: first_name, email',
    )
  })
})
