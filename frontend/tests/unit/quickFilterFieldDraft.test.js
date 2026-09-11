import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { createApp, defineComponent, h, nextTick, ref } from 'vue'

vi.mock('frappe-ui', async () => {
  const { defineComponent, h } = await import('vue')

  // Bare <input> stand-in: mirrors modelValue and passes the listeners the
  // component binds (focus/blur/input) straight through to the element.
  const FormControl = defineComponent({
    inheritAttrs: false,
    props: {
      modelValue: { type: [String, Boolean], default: '' },
      type: { type: String, default: 'text' },
      placeholder: { type: String, default: '' },
    },
    emits: ['update:modelValue'],
    setup(props, { emit, attrs }) {
      return () =>
        h('input', {
          ...attrs,
          value: props.modelValue,
          onInput: (event) => {
            emit('update:modelValue', event.target.value)
            attrs.onInput?.(event)
          },
        })
    },
  })
  const Stub = defineComponent({ setup: () => () => h('div') })

  return { FormControl, DatePicker: Stub, DateTimePicker: Stub }
})

vi.mock('@/components/Controls/Link.vue', async () => {
  const { defineComponent, h } = await import('vue')
  return { default: defineComponent({ setup: () => () => h('div') }) }
})

vi.mock('@/utils', () => ({ getFormat: () => '' }))

const DEBOUNCE = 500

describe('QuickFilterField text draft', () => {
  let root, app, filter, applied, input

  function type(value) {
    input.value = value
    input.dispatchEvent(new Event('input', { bubbles: true }))
  }

  // What ViewControls does after an apply: quickFilterList re-derives a fresh
  // filter object whose value is whatever the list params currently hold.
  async function parentSetsValue(value) {
    filter.value = { ...filter.value, value }
    await nextTick()
  }

  beforeEach(async () => {
    vi.useFakeTimers()
    const { default: QuickFilterField } = await import(
      '@/components/QuickFilterField.vue'
    )

    filter = ref({
      fieldname: 'mobile_no',
      fieldtype: 'Data',
      label: 'Mobile No',
      value: '',
    })
    applied = []

    const Parent = defineComponent({
      setup() {
        return () =>
          h(QuickFilterField, {
            filter: filter.value,
            onApplyQuickFilter: (f, value, onSettled) => {
              applied.push({ value, onSettled })
            },
          })
      },
    })

    root = document.createElement('div')
    document.body.appendChild(root)
    app = createApp(Parent)
    app.mount(root)
    input = root.querySelector('input')
    input.dispatchEvent(new Event('focus'))
  })

  afterEach(() => {
    app.unmount()
    root.remove()
    vi.useRealTimers()
  })

  it('keeps text typed after the debounce fired while the list refreshes', async () => {
    type('12')
    vi.advanceTimersByTime(DEBOUNCE)
    expect(applied.map((a) => a.value)).toEqual(['12'])

    // A keystroke that lands after the commit but before the parent re-derives
    // the filter from the applied params (#2113).
    type('123')
    await parentSetsValue('12')

    expect(input.value).toBe('123')
  })

  it('holds the draft past blur until every emitted apply has settled', async () => {
    type('12')
    vi.advanceTimersByTime(DEBOUNCE)
    await parentSetsValue('12')

    type('123')
    input.dispatchEvent(new Event('blur'))
    vi.advanceTimersByTime(DEBOUNCE)
    await parentSetsValue('123')
    expect(applied.map((a) => a.value)).toEqual(['12', '123'])

    // The first apply's view save finishes late and the parent rebuilds the
    // filter from that stale view while the second apply is still in flight.
    await parentSetsValue('12')
    expect(input.value).toBe('123')

    applied[0].onSettled()
    await nextTick()
    expect(input.value).toBe('123')

    // The second apply lands and settles: the draft now follows the parent.
    await parentSetsValue('123')
    applied[1].onSettled()
    await nextTick()
    expect(input.value).toBe('123')

    // Nothing pending any more, so external changes (e.g. clearing filters)
    // reach the input again.
    await parentSetsValue('')
    expect(input.value).toBe('')
  })
})
