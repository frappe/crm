<!-- Adds or edits a link row of the App menu. The row changes only on Done. -->
<template>
  <Dialog
    v-model:open="open"
    :title="link ? __('Edit link') : __('Add link')"
    size="lg"
  >
    <template #default>
      <form
        id="app-menu-link"
        class="flex flex-col gap-4"
        @submit.prevent="done"
      >
        <div class="flex items-end gap-3">
          <div class="flex w-48 shrink-0 flex-col gap-1.5">
            <span class="text-sm text-ink-gray-6">{{ __('Icon') }}</span>
            <IconPicker
              v-model="pickerIcon"
              :max-icons="1000"
              :placeholder="__('Select an icon...')"
            />
          </div>
          <FormControl
            v-model="draft.label"
            class="flex-1"
            :label="__('Label')"
            :placeholder="__('Sales playbook')"
            required
          />
        </div>
        <FormControl
          v-model="draft.route"
          :label="__('URL')"
          placeholder="https://"
          :description="
            __('A full web address, or a path in this site such as /crm/deals.')
          "
          required
        />
        <FormControl
          v-model="draft.open_in_new_window"
          type="checkbox"
          :label="__('Open in a new tab')"
        />
        <ErrorMessage :message="error" />
      </form>
    </template>
    <template #actions>
      <div class="flex items-center gap-2">
        <Button
          v-if="link"
          variant="subtle"
          theme="red"
          :label="__('Delete')"
          @click="remove"
        />
        <Button class="ml-auto" :label="__('Cancel')" @click="open = false" />
        <Button
          variant="solid"
          type="submit"
          form="app-menu-link"
          :label="__('Done')"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { safeRoute } from '@/composables/appMenu'
import { IconPicker } from 'frappe-ui/experimental'
import { Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  /** The row to edit; unset to add a new link. */
  link: { type: Object, default: null },
})
const emit = defineEmits(['save', 'delete'])
const open = defineModel('open', { type: Boolean, default: false })

const draft = ref({})
const error = ref('')

watch(open, (isOpen) => {
  if (!isOpen) return
  error.value = ''
  draft.value = {
    label: props.link?.label || '',
    icon: props.link?.icon || '',
    route: props.link?.route || '',
    open_in_new_window: Boolean(props.link?.open_in_new_window),
  }
})

watch(draft, () => (error.value = ''), { deep: true })

// The picker is lucide-only; a saved SVG icon stays until a lucide one is picked.
const pickerIcon = computed({
  get: () => (draft.value.icon?.startsWith('<svg') ? '' : draft.value.icon),
  set: (icon) => (draft.value.icon = icon || ''),
})

function done() {
  const label = draft.value.label.trim()
  const route = draft.value.route.trim()
  if (!label) return (error.value = __('Add a label.'))
  if (!safeRoute(route)) {
    return (error.value = __('Enter a web address or a path, such as /crm.'))
  }
  emit('save', {
    ...draft.value,
    label,
    route,
    open_in_new_window: draft.value.open_in_new_window ? 1 : 0,
  })
  open.value = false
}

function remove() {
  emit('delete')
  open.value = false
}
</script>
