<template>
  <Dialog
    v-model:open="show"
    :title="
      editMode
        ? __('Edit View')
        : duplicateMode
          ? __('Duplicate View')
          : __('Create View')
    "
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <div>
          <div class="mb-1.5 block text-base text-ink-gray-5">
            {{ __('View Name') }}
          </div>
          <FormControl
            v-model="view.label"
            size="md"
            type="text"
            :placeholder="__('My Open Deals')"
          />
        </div>
        <div>
          <div class="mb-1.5 block text-base text-ink-gray-5">
            {{ __('Icon') }}
          </div>
          <div class="flex items-center gap-2">
            <!-- legacy views may store an emoji; the lucide picker can't render
                 it, so show it alongside until a lucide icon is picked -->
            <div
              v-if="currentIsEmoji"
              class="grid size-8 shrink-0 place-items-center rounded bg-surface-gray-3 text-lg leading-none"
              :title="__('Current icon')"
            >
              {{ view.icon }}
            </div>
            <IconPicker
              v-model="pickerIcon"
              class="flex-1"
              :max-icons="1000"
              :placeholder="
                currentIsEmoji
                  ? __('Replace with an icon...')
                  : __('Select an icon...')
              "
            />
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          variant="solid"
          :disabled="!view.label?.trim()"
          :label="
            editMode
              ? __('Save Changes')
              : duplicateMode
                ? __('Duplicate')
                : __('Create')
          "
          @click="() => (editMode ? update() : create())"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { IconPicker } from 'frappe-ui/icons'
import { isEmoji } from '@/utils'
import { call } from 'frappe-ui'
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  options: {
    type: Object,
    default: () => ({ afterCreate: () => {}, afterUpdate: () => {} }),
  },
})

const show = defineModel({ type: Boolean })
const view = defineModel('view', { type: Object, default: () => ({}) })

// frappe-ui's IconPicker is lucide-only. Legacy views may store an emoji, which
// the picker can't render — hide non-lucide values from it (showing the
// placeholder) while keeping the stored icon, so a no-op edit preserves the
// emoji and picking a lucide icon migrates it.
const currentIsEmoji = computed(() => isEmoji(view.value?.icon || ''))
const pickerIcon = computed({
  get: () => {
    const icon = view.value?.icon
    return !icon || isEmoji(icon) ? '' : icon
  },
  set: (value) => {
    view.value.icon = value || ''
  },
})

const editMode = ref(false)
const duplicateMode = ref(false)

const _view = ref({
  name: '',
  label: '',
  type: 'list',
  icon: '',
  filters: {},
  order_by: 'modified desc',
  columns: '',
  rows: '',
})

async function create() {
  view.value.doctype = props.doctype
  let v = await call(
    'crm.fcrm.doctype.crm_view_settings.crm_view_settings.create',
    { view: view.value },
  )
  show.value = false
  props.options.afterCreate?.(v)
}

async function update() {
  view.value.doctype = props.doctype
  await call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.update', {
    view: view.value,
  })
  show.value = false
  props.options.afterUpdate?.(view.value)
}

watch(show, (value) => {
  if (!value) return
  editMode.value = false
  duplicateMode.value = false
  nextTick(() => {
    _view.value = { ...view.value }
    if (_view.value.mode === 'edit') {
      editMode.value = true
    } else if (_view.value.mode === 'duplicate') {
      duplicateMode.value = true
    }
  })
})
</script>
