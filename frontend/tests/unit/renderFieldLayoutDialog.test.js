import { describe, it, expect, beforeEach } from 'vitest'
import {
  fieldLayoutDialogs,
  renderFieldLayoutDialog,
} from '@/utils/renderFieldLayoutDialog'

describe('renderFieldLayoutDialog', () => {
  beforeEach(() => {
    fieldLayoutDialogs.value = []
  })

  // ── Core promise behavior ──

  it('returns a Promise', () => {
    const result = renderFieldLayoutDialog({ title: 'Test' })
    expect(result).toBeInstanceOf(Promise)
  })

  it('pushes a dialog entry to fieldLayoutDialogs', () => {
    renderFieldLayoutDialog({ title: 'Test Dialog' })
    expect(fieldLayoutDialogs.value).toHaveLength(1)
    expect(fieldLayoutDialogs.value[0].props.title).toBe('Test Dialog')
    expect(fieldLayoutDialogs.value[0].key).toBeTruthy()
  })

  it('resolves with data when onResolve is called', async () => {
    const promise = renderFieldLayoutDialog({ title: 'Test' })
    fieldLayoutDialogs.value[0].props.onResolve({ name: 'Alice' })
    expect(await promise).toEqual({ name: 'Alice' })
  })

  it('resolves with null on cancel', async () => {
    const promise = renderFieldLayoutDialog({ title: 'Test' })
    fieldLayoutDialogs.value[0].props.onResolve(null)
    expect(await promise).toBeNull()
  })

  it('only resolves once even if onResolve is called multiple times', async () => {
    const promise = renderFieldLayoutDialog({ title: 'Test' })
    const entry = fieldLayoutDialogs.value[0]
    entry.props.onResolve({ first: true })
    entry.props.onResolve({ second: true })
    expect(await promise).toEqual({ first: true })
  })

  it('removes dialog entry after resolve (with delay)', async () => {
    vi.useFakeTimers()
    const promise = renderFieldLayoutDialog({ title: 'Test' })
    expect(fieldLayoutDialogs.value).toHaveLength(1)
    fieldLayoutDialogs.value[0].props.onResolve({ done: true })
    expect(fieldLayoutDialogs.value).toHaveLength(1)
    vi.advanceTimersByTime(300)
    expect(fieldLayoutDialogs.value).toHaveLength(0)
    vi.useRealTimers()
    await promise
  })

  // ── Options passthrough ──

  it('passes all core options through to dialog props', () => {
    renderFieldLayoutDialog({
      title: 'My Dialog',
      doctype: 'CRM Lost Reason',
      size: 'lg',
      defaults: { lead: 'LEAD-001' },
      required: ['lost_reason'],
      actions: [{ label: 'Save', variant: 'solid' }],
    })

    const props = fieldLayoutDialogs.value[0].props
    expect(props.title).toBe('My Dialog')
    expect(props.doctype).toBe('CRM Lost Reason')
    expect(props.size).toBe('lg')
    expect(props.defaults).toEqual({ lead: 'LEAD-001' })
    expect(props.required).toEqual(['lost_reason'])
    expect(props.actions).toEqual([{ label: 'Save', variant: 'solid' }])
  })

  it('passes fieldnames option', () => {
    renderFieldLayoutDialog({
      title: 'Pick Fields',
      doctype: 'CRM Lead',
      fieldnames: ['first_name', 'email', 'phone'],
    })
    const props = fieldLayoutDialogs.value[0].props
    expect(props.fieldnames).toEqual(['first_name', 'email', 'phone'])
  })

  it('passes inline fields', () => {
    renderFieldLayoutDialog({
      title: 'Inline',
      fields: [
        { fieldname: 'territory', fieldtype: 'Data', label: 'Territory' },
      ],
    })
    expect(fieldLayoutDialogs.value[0].props.fields).toHaveLength(1)
  })

  it('passes full tabs layout', () => {
    const tabs = [
      {
        name: 'tab1',
        label: 'Details',
        sections: [
          {
            name: 'sec1',
            label: 'Basic',
            columns: [
              {
                name: 'col1',
                fields: [
                  { fieldname: 'name', fieldtype: 'Data', label: 'Name' },
                ],
              },
              {
                name: 'col2',
                fields: [
                  { fieldname: 'email', fieldtype: 'Data', label: 'Email' },
                ],
              },
            ],
          },
        ],
      },
    ]
    renderFieldLayoutDialog({ title: 'Full Layout', tabs })
    const props = fieldLayoutDialogs.value[0].props
    expect(props.tabs).toHaveLength(1)
    expect(props.tabs[0].sections[0].columns).toHaveLength(2)
  })

  // ── onSubmit / onCancel passthrough ──

  it('passes onSubmit function through to dialog props', () => {
    const handler = vi.fn()
    renderFieldLayoutDialog({
      title: 'Test',
      fields: [{ fieldname: 'x', fieldtype: 'Data', label: 'X' }],
      onSubmit: handler,
    })
    expect(fieldLayoutDialogs.value[0].props.onSubmit).toBe(handler)
  })

  it('passes onCancel function through to dialog props', () => {
    const handler = vi.fn()
    renderFieldLayoutDialog({
      title: 'Test',
      fields: [{ fieldname: 'x', fieldtype: 'Data', label: 'X' }],
      onCancel: handler,
    })
    expect(fieldLayoutDialogs.value[0].props.onCancel).toBe(handler)
  })

  it('promise resolves with null when onCancel is provided and dialog is cancelled', async () => {
    const cancelHandler = vi.fn()
    const promise = renderFieldLayoutDialog({
      title: 'Test',
      onCancel: cancelHandler,
    })
    // Simulate cancel — onResolve called with null
    fieldLayoutDialogs.value[0].props.onResolve(null)
    expect(await promise).toBeNull()
  })

  it('promise still resolves with data even when onSubmit is provided', async () => {
    const submitHandler = vi.fn()
    const promise = renderFieldLayoutDialog({
      title: 'Test',
      onSubmit: submitHandler,
    })
    // Simulate submit — onResolve called with data
    fieldLayoutDialogs.value[0].props.onResolve({ foo: 'bar' })
    expect(await promise).toEqual({ foo: 'bar' })
  })

  // ── Concurrent dialogs ──

  it('supports multiple concurrent dialogs', () => {
    renderFieldLayoutDialog({ title: 'Dialog 1' })
    renderFieldLayoutDialog({ title: 'Dialog 2' })
    expect(fieldLayoutDialogs.value).toHaveLength(2)
    expect(fieldLayoutDialogs.value[0].key).not.toBe(
      fieldLayoutDialogs.value[1].key,
    )
  })

  it('resolves concurrent dialogs independently', async () => {
    const p1 = renderFieldLayoutDialog({ title: 'D1' })
    const p2 = renderFieldLayoutDialog({ title: 'D2' })
    fieldLayoutDialogs.value[1].props.onResolve({ from: 'D2' })
    fieldLayoutDialogs.value[0].props.onResolve({ from: 'D1' })
    expect(await p1).toEqual({ from: 'D1' })
    expect(await p2).toEqual({ from: 'D2' })
  })

  // ── Actions passthrough ──

  it('passes custom actions array', () => {
    const actions = [
      { label: 'Approve', variant: 'solid' },
      { label: 'Reject', variant: 'subtle', theme: 'red' },
      { label: 'Cancel' },
    ]
    renderFieldLayoutDialog({ title: 'Review', actions })
    expect(fieldLayoutDialogs.value[0].props.actions).toEqual(actions)
  })

  it('works without actions or onSubmit (default Submit via promise)', () => {
    renderFieldLayoutDialog({ title: 'Simple' })
    const props = fieldLayoutDialogs.value[0].props
    expect(props.actions).toBeUndefined()
    expect(props.onSubmit).toBeUndefined()
  })

  // ── submitLabel / cancelLabel passthrough ──

  it('passes submitLabel through to dialog props', () => {
    renderFieldLayoutDialog({
      title: 'Test',
      fields: [{ fieldname: 'x', fieldtype: 'Data', label: 'X' }],
      submitLabel: 'Save',
    })
    expect(fieldLayoutDialogs.value[0].props.submitLabel).toBe('Save')
  })

  it('passes cancelLabel through to dialog props', () => {
    renderFieldLayoutDialog({
      title: 'Test',
      fields: [{ fieldname: 'x', fieldtype: 'Data', label: 'X' }],
      cancelLabel: 'Discard',
    })
    expect(fieldLayoutDialogs.value[0].props.cancelLabel).toBe('Discard')
  })

  it('does not pass cancelLabel when not provided', () => {
    renderFieldLayoutDialog({ title: 'Test' })
    expect(fieldLayoutDialogs.value[0].props.cancelLabel).toBeUndefined()
  })

  // ── onResolve is separate from user options ──

  it('onResolve does not collide with user onSubmit', async () => {
    const submitFn = vi.fn()
    const promise = renderFieldLayoutDialog({
      title: 'Test',
      onSubmit: submitFn,
    })
    const entry = fieldLayoutDialogs.value[0]
    // onResolve is our internal hook, onSubmit is the user's
    expect(entry.props.onResolve).toBeTypeOf('function')
    expect(entry.props.onSubmit).toBe(submitFn)
    entry.props.onResolve({ data: 1 })
    expect(await promise).toEqual({ data: 1 })
  })
})
