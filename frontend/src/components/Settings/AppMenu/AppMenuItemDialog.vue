<!-- Adds or edits a link or a submenu of the App menu. The row changes only on Done. -->
<template>
  <Dialog v-model:open="open" :title="title" size="lg">
    <template #default>
      <form
        id="app-menu-item"
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
            :placeholder="
              isSubmenu ? __('Team resources') : __('Sales playbook')
            "
            required
          />
        </div>
        <template v-if="isSubmenu">
          <p class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Drag links under it in the list, or set Show in on a link to put it here.',
              )
            }}
          </p>
        </template>
        <template v-else>
          <FormControl
            v-model="draft.route"
            :label="__('URL')"
            placeholder="https://"
            :description="
              __(
                'A full web address, or a path in this site such as /crm/deals.',
              )
            "
            required
          />
          <FormControl
            v-model="draft.parent_submenu"
            type="select"
            :label="__('Show in')"
            :options="showInOptions"
          />
          <FormControl
            v-model="draft.open_in_new_window"
            type="checkbox"
            :label="__('Open in a new tab')"
          />
        </template>
        <ErrorMessage :message="error" />
      </form>
    </template>
    <template #actions>
      <div class="flex flex-col gap-3">
        <div class="flex items-center gap-2">
          <Button
            v-if="item"
            variant="subtle"
            theme="red"
            :label="__('Delete')"
            @click="remove"
          />
          <Button class="ml-auto" :label="__('Cancel')" @click="open = false" />
          <Button
            variant="solid"
            type="submit"
            form="app-menu-item"
            :label="__('Done')"
          />
        </div>
        <p
          v-if="item && isSubmenu && linkCount"
          class="border-t border-outline-gray-1 pt-3 text-p-sm text-ink-gray-6"
        >
          {{
            linkCount === 1
              ? __(
                  'Delete keeps its link. It moves to the top level, where the submenu was.',
                )
              : __(
                  'Delete keeps its {0} links. They move to the top level, where the submenu was.',
                  [linkCount],
                )
          }}
        </p>
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
  /** The row to edit; unset to add a new one of `type`. */
  item: { type: Object, default: null },
  /** `Route` for a link or `Submenu`, used when adding. */
  type: { type: String, default: 'Route' },
  /** The submenu key the link is in now; empty for the top level. */
  parentSubmenu: { type: String, default: '' },
  /** Submenus a link can go in, as `{ label, value }`. */
  submenus: { type: Array, default: () => [] },
  /** How many links the edited submenu holds. */
  linkCount: { type: Number, default: 0 },
})
const emit = defineEmits(['save', 'delete'])
const open = defineModel('open', { type: Boolean, default: false })

const draft = ref({})
const error = ref('')

const isSubmenu = computed(() => (props.item?.type || props.type) === 'Submenu')

const title = computed(() => {
  if (isSubmenu.value) {
    return props.item ? __('Edit submenu') : __('Add submenu')
  }
  return props.item ? __('Edit link') : __('Add link')
})

const showInOptions = computed(() => [
  { label: __('Top level'), value: '' },
  ...props.submenus,
])

watch(open, (isOpen) => {
  if (!isOpen) return
  error.value = ''
  draft.value = {
    label: props.item?.label || '',
    icon: props.item?.icon || '',
    route: props.item?.route || '',
    open_in_new_window: Boolean(props.item?.open_in_new_window),
    parent_submenu: props.parentSubmenu,
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
  if (!label) return (error.value = __('Add a label.'))
  if (isSubmenu.value) {
    emit('save', { label, icon: draft.value.icon })
    open.value = false
    return
  }
  const route = draft.value.route.trim()
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
