/* eslint-disable vue/one-component-per-file -- Route and dialog fixtures exercise the global modal host. */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createApp, h, nextTick, onMounted } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'
import DoctypeModals from '@/components/Modals/DoctypeModals.vue'
import { useDoctypeModal } from '@/composables/doctypeModal'

const modal = vi.hoisted(() => ({ emit: null }))

vi.mock('@/components/Modals/DoctypeModal.vue', async () => {
  const { defineComponent, h } = await import('vue')
  return {
    default: defineComponent({
      props: {
        modelValue: Boolean,
        doctypeTitle: { type: String, default: '' },
        doctype: { type: String, default: '' },
        docname: { type: String, default: '' },
        defaults: { type: Object, default: () => ({}) },
      },
      emits: ['update:modelValue', 'afterInsert', 'afterUpdate'],
      setup(_, { emit }) {
        modal.emit = emit
        return () => h('div', { role: 'dialog' }, 'Address dialog')
      },
    }),
  }
})

describe('global doctype dialog navigation', () => {
  let app, container, router
  const doctypeModal = useDoctypeModal()

  beforeEach(async () => {
    doctypeModal.show.value = false
    modal.emit = null
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/organizations/:name', component: { render: () => null } },
      ],
    })
    await router.push('/organizations/A')
    container = document.createElement('div')
    document.body.appendChild(container)
    app = createApp({
      render: () => [
        h(RouterView, { key: router.currentRoute.value.fullPath }),
        h(DoctypeModals),
      ],
    })
    app.use(router)
    await router.isReady()
    app.mount(container)
  })

  afterEach(() => {
    app.unmount()
    container.remove()
    doctypeModal.show.value = false
  })

  async function open(callbacks = {}) {
    doctypeModal.showModal({ doctype: 'Address', callbacks })
    await nextTick()
    expect(container.querySelector('[role="dialog"]')).not.toBeNull()
  }

  it.each([
    '/organizations/B',
    '/organizations/A?tab=details',
    '/organizations/A#activity',
  ])('closes the dialog when the page changes to %s', async (path) => {
    await open()
    await router.push(path)
    await nextTick()
    expect(doctypeModal.show.value).toBe(false)
    expect(container.querySelector('[role="dialog"]')).toBeNull()
  })

  it('clears callbacks belonging to the previous page', async () => {
    const afterInsert = vi.fn()
    const afterUpdate = vi.fn()
    await open({ afterInsert, afterUpdate })
    await router.push('/organizations/B')
    doctypeModal.triggerCallback('afterInsert', { name: 'Old address' })
    doctypeModal.triggerCallback('afterUpdate', { name: 'Old address' })
    expect(afterInsert).not.toHaveBeenCalled()
    expect(afterUpdate).not.toHaveBeenCalled()
  })

  it('clears old callbacks before afterEach navigation callbacks run', async () => {
    const afterInsert = vi.fn()
    await open({ afterInsert })
    router.afterEach(() => {
      doctypeModal.triggerCallback('afterInsert', { name: 'Old address' })
    })
    await router.push('/organizations/B')
    expect(afterInsert).not.toHaveBeenCalled()
  })

  it('allows the next page to open its own dialog on mount', async () => {
    const newCallback = vi.fn()
    router.addRoute({
      path: '/next',
      component: {
        setup() {
          onMounted(() =>
            doctypeModal.showModal({
              doctype: 'Address',
              callbacks: { afterInsert: newCallback },
            }),
          )
          return () => null
        },
      },
    })
    await open()
    await router.push('/next')
    await nextTick()
    expect(doctypeModal.show.value).toBe(true)
    modal.emit('afterInsert', { name: 'New address' })
    expect(newCallback).toHaveBeenCalledExactlyOnceWith({ name: 'New address' })
  })

  it('keeps the dialog open when navigation is cancelled', async () => {
    router.beforeEach(() => false)
    await open()
    await router.push('/organizations/B')
    expect(doctypeModal.show.value).toBe(true)
    expect(container.querySelector('[role="dialog"]')).not.toBeNull()
  })

  it('keeps the dialog open for duplicate navigation', async () => {
    await open()
    await router.push('/organizations/A')
    expect(doctypeModal.show.value).toBe(true)
    expect(container.querySelector('[role="dialog"]')).not.toBeNull()
  })

  it.each(['afterInsert', 'afterUpdate'])(
    'preserves normal %s callbacks',
    async (event) => {
      const callback = vi.fn()
      await open({ [event]: callback })
      const address = { name: 'New address' }
      modal.emit(event, address)
      expect(callback).toHaveBeenCalledExactlyOnceWith(address)
    },
  )

  it('does not route a late event from the old dialog to a new dialog', async () => {
    const oldCallback = vi.fn()
    const newCallback = vi.fn()
    await open({ afterInsert: oldCallback })
    const oldEmit = modal.emit
    await router.push('/organizations/B')
    await nextTick()
    await open({ afterInsert: newCallback })
    oldEmit('afterInsert', { name: 'Old address' })
    expect(oldCallback).not.toHaveBeenCalled()
    expect(newCallback).not.toHaveBeenCalled()
    modal.emit('afterInsert', { name: 'New address' })
    expect(newCallback).toHaveBeenCalledExactlyOnceWith({ name: 'New address' })
  })
})
