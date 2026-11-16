import { h, isVNode } from 'vue'

const { toast } = vi.hoisted(() => {
  const toast = vi.fn()
  toast.success = vi.fn()
  toast.error = vi.fn()
  return { toast }
})

vi.mock('frappe-ui', () => ({ toast }))
vi.mock('@/components/Icon.vue', () => ({ default: { name: 'Icon' } }))

import { createToast, scriptToast } from '@/utils/scriptToast'

beforeEach(() => vi.clearAllMocks())

describe('createToast', () => {
  it('shows message with the toast of its type', () => {
    createToast({ message: 'Saved', type: 'success' })
    expect(toast.success).toHaveBeenCalledWith('Saved', {
      description: undefined,
    })
  })

  it('reads the older title and text shape', () => {
    createToast({ title: 'Lead created', text: 'Assigned to you' })
    expect(toast).toHaveBeenCalledWith('Lead created', {
      description: 'Assigned to you',
    })
  })

  it('turns durations in seconds into milliseconds', () => {
    createToast({ message: 'a', duration: 2 })
    createToast({ message: 'b', timeout: 3 })
    expect(toast.mock.calls[0][1].duration).toBe(2000)
    expect(toast.mock.calls[1][1].duration).toBe(3000)
  })

  it('keeps a toast open when duration is 0', () => {
    createToast({ message: 'a', duration: 0 })
    expect(toast.mock.calls[0][1].duration).toBe(Infinity)
  })

  it('locks the toast when closable is false', () => {
    createToast({ message: 'a', duration: 2, closable: false })
    expect(toast.mock.calls[0][1]).toMatchObject({
      duration: Infinity,
      closeButton: false,
      dismissible: false,
    })
  })

  it('passes other options such as id and action through', () => {
    const action = { label: 'Undo', onClick() {} }
    createToast({ message: 'a', id: 'x', action })
    expect(toast.mock.calls[0][1]).toMatchObject({ id: 'x', action })
  })

  it('renders an icon name with the Icon component', () => {
    createToast({ message: 'a', icon: 'check', iconClasses: 'text-green' })
    const vnode = toast.mock.calls[0][1].icon()
    expect(vnode.type.name).toBe('Icon')
    expect(vnode.props).toMatchObject({
      icon: 'check',
      class: 'size-4 text-green',
    })
  })

  it('wraps a vnode icon in a render function', () => {
    const icon = h('span')
    createToast({ message: 'a', icon })
    expect(isVNode(toast.mock.calls[0][1].icon())).toBe(true)
  })
})

describe('scriptToast', () => {
  it('maps the object form to createToast', () => {
    scriptToast({ title: 'Oops', text: 'Try again', type: 'error' })
    expect(toast.error).toHaveBeenCalledWith('Oops', {
      description: 'Try again',
    })
  })

  it('passes a plain message straight to toast', () => {
    scriptToast('Hi', { duration: 500 })
    expect(toast).toHaveBeenCalledWith('Hi', { duration: 500 })
  })

  it('keeps the typed helpers', () => {
    scriptToast.success('Done')
    expect(toast.success).toHaveBeenCalledWith('Done')
  })
})
