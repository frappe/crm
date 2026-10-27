import {
  catalog,
  isRegistered,
  newItem,
  withMinWidth,
} from '@/components/Home/widgets'
import { usersStore } from '@/stores/users'
import { copy } from '@/utils'
import { call, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

function homeApi(target) {
  if (target === 'mine') {
    return {
      get: () => call('crm.api.home.get_layout'),
      save: (layout) => call('crm.api.home.save_layout', { layout }),
      reset: () => call('crm.api.home.reset_layout'),
    }
  }
  const role = target
  return {
    get: () => call('crm.api.home.get_default_layout', { role }),
    save: (layout) =>
      call('crm.api.home.save_default_layout', { role, layout }),
    reset: () => call('crm.api.home.reset_default_layout', { role }),
  }
}

export function useHomeLayout() {
  const { isManager } = usersStore()

  const target = ref('mine')
  const items = ref([])
  const saved = ref([])
  const loading = ref(false)
  const editing = ref(false)

  const endpoints = () => homeApi(target.value)

  const visibleItems = computed({
    get: () => items.value.filter((item) => isRegistered(item.name)),
    set: (visible) => {
      const hidden = items.value.filter((item) => !isRegistered(item.name))
      items.value = [...visible, ...hidden]
    },
  })

  const availableWidgets = computed(() =>
    catalog({
      manager:
        target.value === 'mine' ? isManager() : target.value === 'manager',
      items: items.value,
    }),
  )

  const dirty = computed(
    () => JSON.stringify(items.value) !== JSON.stringify(saved.value),
  )

  async function load(nextTarget = 'mine') {
    target.value = nextTarget
    loading.value = true
    try {
      apply(await endpoints().get())
    } finally {
      loading.value = false
    }
  }

  function apply(home) {
    saved.value = home.layout.map((item) => withMinWidth(item))
    items.value = copy(home.layout)
  }

  async function edit(nextTarget = 'mine') {
    if (nextTarget !== target.value) await load(nextTarget)
    editing.value = true
  }

  async function finish() {
    editing.value = false
    if (target.value !== 'mine') await load('mine')
  }

  function cancel() {
    items.value = copy(saved.value)
    finish()
  }

  async function save() {
    await run(() => endpoints().save(items.value))
  }

  async function reset() {
    await run(() => endpoints().reset())
  }

  async function run(request) {
    try {
      apply(await request())
      await finish()
    } catch (error) {
      toast.error(error.messages?.[0] || __('Could not save Home layout'))
    }
  }

  function addWidget(widget) {
    items.value = [...items.value, newItem(widget, items.value)]
  }

  async function updateConfig(item, config) {
    item.config = config
    if (editing.value) return
    await save()
    items.value = copy(saved.value)
  }

  return {
    target,
    loading,
    editing,
    dirty,
    visibleItems,
    availableWidgets,
    load,
    edit,
    cancel,
    save,
    reset,
    addWidget,
    updateConfig,
  }
}
