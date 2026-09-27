import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createApp, defineComponent, h, nextTick, ref } from 'vue'

const state = vi.hoisted(() => ({
  serverData: null,
  uploads: [],
  uploadResult: null,
}))

vi.mock('frappe-ui', async () => {
  const { defineComponent, h, reactive } = await import('vue')

  return {
    useCall: vi.fn(() => reactive({ data: state.serverData })),
    toast: { warning: vi.fn(), error: vi.fn() },
    FormControl: defineComponent({
      props: { modelValue: Boolean, label: String },
      emits: ['update:modelValue'],
      setup(props, { emit }) {
        return () =>
          h('label', [
            h('input', {
              type: 'checkbox',
              checked: props.modelValue,
              onChange: (e) => emit('update:modelValue', e.target.checked),
            }),
            props.label,
          ])
      },
    }),
    CircularProgressBar: defineComponent({ setup: () => () => h('div') }),
  }
})

vi.mock('@/utils', () => ({
  convertSize: (size) => `${size} B`,
  formatDate: () => '',
}))

vi.mock('@/composables/settings', async () => {
  const { ref } = await import('vue')
  return { isMobileView: ref(false) }
})

vi.mock('@/components/FilesUploader/filesUploaderHandler', () => ({
  default: class {
    on() {}
    upload(file, args) {
      state.uploads.push(args)
      return state.uploadResult(file)
    }
  },
}))

const Dialog = defineComponent({
  props: { open: Boolean },
  setup(props, { slots }) {
    return () => props.open && h('div', [slots.default?.(), slots.actions?.()])
  },
})

const Button = defineComponent({
  props: { label: String, disabled: Boolean },
  setup(props) {
    return () => h('button', { disabled: props.disabled }, props.label)
  },
})

const ErrorMessage = defineComponent({
  props: { message: String },
  setup(props) {
    return () => h('p', { 'data-testid': 'error' }, props.message)
  },
})

const serverDefaults = {
  allowed_file_types: 'pdf\npng',
  max_file_size: 1000,
  max_number_of_files: 0,
  make_attachments_public: true,
}

const mounted = []

async function mountUploader(props = {}) {
  const { default: FilesUploader } =
    await import('@/components/FilesUploader/FilesUploader.vue')

  const root = document.createElement('div')
  document.body.appendChild(root)

  const show = ref(true)
  const afterEvents = []

  const Parent = defineComponent({
    setup() {
      return () =>
        h(FilesUploader, {
          modelValue: show.value,
          'onUpdate:modelValue': (value) => (show.value = value),
          doctype: 'CRM Deal',
          docname: 'DEAL-001',
          onAfter: (uploaded) => afterEvents.push(uploaded),
          ...props,
        })
    },
  })

  const app = createApp(Parent)
  app.config.globalProperties.__ = globalThis.__
  app.component('Dialog', Dialog)
  app.component('Button', Button)
  app.component('ErrorMessage', ErrorMessage)
  app.component('TextInput', defineComponent({ setup: () => () => h('input') }))
  app.mount(root)
  await nextTick()

  const unmount = () => {
    app.unmount()
    root.remove()
  }
  mounted.push(unmount)

  return { root, show, afterEvents, unmount }
}

function pdf(name, size = 10) {
  return new File(['x'.repeat(size)], name, { type: 'application/pdf' })
}

async function addFiles(root, files) {
  const input = root.querySelector('input[type="file"]')
  Object.defineProperty(input, 'files', { value: files, configurable: true })
  input.dispatchEvent(new Event('change'))
  await nextTick()
}

function findButton(root, label) {
  return [...root.querySelectorAll('button')].find(
    (button) => button.textContent === label,
  )
}

function privateCheckboxes(root) {
  return [...root.querySelectorAll('input[type="checkbox"]')]
}

function flushPromises() {
  return new Promise((resolve) => setTimeout(resolve))
}

describe('FilesUploader', () => {
  beforeEach(async () => {
    const { toast } = await import('frappe-ui')
    toast.warning.mockClear()
    state.serverData = { ...serverDefaults }
    state.uploads = []
    state.uploadResult = (file) => Promise.resolve({ file_name: file.name })
  })

  afterEach(() => {
    mounted.splice(0).forEach((unmount) => unmount())
  })

  it('loads the upload settings for its doctype', async () => {
    const { useCall } = await import('frappe-ui')
    await mountUploader()

    expect(useCall).toHaveBeenLastCalledWith(
      expect.objectContaining({ params: { doctype: 'CRM Deal' } }),
    )
  })

  it('limits the file picker to the allowed file types', async () => {
    const { root } = await mountUploader()

    expect(root.querySelector('input[type="file"]').accept).toBe('.pdf, .png')
  })

  it('starts new files as public when the doctype makes attachments public', async () => {
    const { root } = await mountUploader()
    await addFiles(root, [pdf('a.pdf')])

    expect(privateCheckboxes(root).map((box) => box.checked)).toEqual([false])
  })

  it('starts new files as private when the doctype does not make attachments public', async () => {
    state.serverData.make_attachments_public = false
    const { root } = await mountUploader()
    await addFiles(root, [pdf('a.pdf')])

    expect(privateCheckboxes(root).map((box) => box.checked)).toEqual([true])
  })

  it('applies the upload settings again when the uploader is opened a second time', async () => {
    const first = await mountUploader()
    first.unmount()

    const { root } = await mountUploader()
    await addFiles(root, [pdf('a.pdf')])

    expect(root.querySelector('input[type="file"]').accept).toBe('.pdf, .png')
    expect(privateCheckboxes(root).map((box) => box.checked)).toEqual([false])
  })

  it('uses the passed in options until the server answers', async () => {
    state.serverData = null
    const { root } = await mountUploader({
      options: {
        restrictions: { allowedFileTypes: ['.csv'] },
        makeAttachmentsPublic: true,
      },
    })
    await addFiles(root, [
      new File(['x'], 'a.csv', { type: 'text/csv' }),
      pdf('b.pdf'),
    ])

    expect(root.querySelector('input[type="file"]').accept).toBe('.csv')
    expect(privateCheckboxes(root).map((box) => box.checked)).toEqual([false])
  })

  it('skips files with a type that is not allowed', async () => {
    const { toast } = await import('frappe-ui')
    const { root } = await mountUploader()
    await addFiles(root, [
      pdf('a.pdf'),
      new File(['x'], 'b.exe', { type: 'application/octet-stream' }),
    ])

    expect(privateCheckboxes(root)).toHaveLength(1)
    expect(root.textContent).toContain('a.pdf')
    expect(toast.warning).toHaveBeenCalledWith(
      'File "b.exe" was skipped because of invalid file type',
    )
  })

  it('skips files larger than the size limit', async () => {
    const { toast } = await import('frappe-ui')
    const { root } = await mountUploader()
    await addFiles(root, [pdf('small.pdf', 10), pdf('big.pdf', 2000)])

    expect(privateCheckboxes(root)).toHaveLength(1)
    expect(root.textContent).toContain('small.pdf')
    expect(toast.warning).toHaveBeenCalledTimes(1)
  })

  it('lets passed in restrictions override the server settings', async () => {
    const { toast } = await import('frappe-ui')
    const { root } = await mountUploader({
      options: { restrictions: { maxNumberOfFiles: 1 } },
    })
    await addFiles(root, [pdf('a.pdf'), pdf('b.pdf')])

    expect(privateCheckboxes(root)).toHaveLength(1)
    expect(root.querySelector('input[type="file"]').accept).toBe('.pdf, .png')
    expect(toast.warning).toHaveBeenCalledWith(
      'File "b.pdf" was skipped because only 1 uploads are allowed for DocType "CRM Deal"',
    )
  })

  it('switches every file between private and public', async () => {
    const { root } = await mountUploader()
    await addFiles(root, [pdf('a.pdf'), pdf('b.pdf')])

    findButton(root, 'Set all as private').click()
    await nextTick()
    expect(privateCheckboxes(root).map((box) => box.checked)).toEqual([
      true,
      true,
    ])

    findButton(root, 'Set all as public').click()
    await nextTick()
    expect(privateCheckboxes(root).map((box) => box.checked)).toEqual([
      false,
      false,
    ])
  })

  it('removes all added files', async () => {
    const { root } = await mountUploader()
    await addFiles(root, [pdf('a.pdf'), pdf('b.pdf')])

    findButton(root, 'Remove All').click()
    await nextTick()

    expect(privateCheckboxes(root)).toHaveLength(0)
    expect(findButton(root, 'Attach').disabled).toBe(true)
  })

  it('uploads every file to the record and closes when done', async () => {
    const { root, show, afterEvents } = await mountUploader({
      options: { folder: 'Home/Attachments' },
    })
    await addFiles(root, [pdf('a.pdf'), pdf('b.pdf')])
    privateCheckboxes(root)[1].click()
    await nextTick()

    findButton(root, 'Attach').click()
    await flushPromises()

    expect(state.uploads).toEqual([
      expect.objectContaining({
        doctype: 'CRM Deal',
        docname: 'DEAL-001',
        folder: 'Home/Attachments',
        private: false,
      }),
      expect.objectContaining({ private: true }),
    ])
    expect(afterEvents).toEqual([
      [{ file_name: 'a.pdf' }, { file_name: 'b.pdf' }],
    ])
    expect(show.value).toBe(false)
  })

  it('shows the error and stays open when an upload fails', async () => {
    state.uploadResult = () => Promise.reject('Size exceeds the limit')
    const { root, show, afterEvents } = await mountUploader()
    await addFiles(root, [pdf('a.pdf')])

    findButton(root, 'Attach').click()
    await flushPromises()

    expect(root.querySelector('[data-testid="error"]').textContent).toBe(
      'Size exceeds the limit',
    )
    expect(afterEvents).toEqual([])
    expect(show.value).toBe(true)
  })
})
