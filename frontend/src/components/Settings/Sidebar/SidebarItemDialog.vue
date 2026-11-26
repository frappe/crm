<!-- Adds a DocType to the sidebar, or edits an item's label and icon. The row changes only on Done. -->
<template>
  <Dialog v-model:open="open" :title="title" size="lg">
    <template #default>
      <form
        id="sidebar-item"
        class="flex flex-col gap-4"
        @submit.prevent="done"
      >
        <Link
          v-if="!item"
          v-model="draft.dt"
          doctype="DocType"
          :label="__('DocType')"
          :placeholder="__('Select a DocType')"
          :filters="doctypeFilters"
          required
        />
        <div class="flex items-end gap-3">
          <div class="flex w-48 shrink-0 flex-col gap-1.5">
            <span class="text-sm text-ink-gray-6">{{ __('Icon') }}</span>
            <IconPicker
              v-model="draft.icon"
              :max-icons="1000"
              :placeholder="
                item?.is_standard
                  ? __('Built-in icon')
                  : __('Select an icon...')
              "
            />
          </div>
          <FormControl
            v-model="draft.label"
            class="flex-1"
            :label="__('Label')"
            :placeholder="draft.dt || item?.label"
          />
        </div>
        <ErrorMessage :message="error" />
      </form>
    </template>
    <template #actions>
      <div class="flex items-center gap-2">
        <Button
          v-if="item && !item.is_standard"
          variant="subtle"
          theme="red"
          :label="__('Remove')"
          @click="remove"
        />
        <Button class="ml-auto" :label="__('Cancel')" @click="open = false" />
        <Button
          variant="solid"
          type="submit"
          form="sidebar-item"
          :label="item ? __('Done') : __('Add')"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { IconPicker } from 'frappe-ui/experimental'
import { Dialog, ErrorMessage, FormControl } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  /** The row to edit; unset to add a DocType. */
  item: { type: Object, default: null },
  /** DocTypes already in the sidebar, left out of the picker. */
  usedDoctypes: { type: Array, default: () => [] },
})
const emit = defineEmits(['save', 'delete'])
const open = defineModel('open', { type: Boolean, default: false })

const draft = ref({})
const error = ref('')

const title = computed(() => {
  if (!props.item) return __('Add DocType')
  return props.item.is_standard ? __('Edit page') : __('Edit DocType')
})

// Singles, child tables and virtual DocTypes have no list to open.
const doctypeFilters = computed(() => ({
  istable: 0,
  issingle: 0,
  is_virtual: 0,
  name: ['not in', props.usedDoctypes],
}))

watch(open, (isOpen) => {
  if (!isOpen) return
  error.value = ''
  draft.value = {
    dt: props.item?.dt || '',
    label: props.item?.label || '',
    icon: props.item?.icon || '',
  }
})

watch(draft, () => (error.value = ''), { deep: true })

function done() {
  const label = draft.value.label.trim() || draft.value.dt
  if (!props.item && !draft.value.dt) {
    return (error.value = __('Choose a DocType.'))
  }
  if (!label) return (error.value = __('Add a label.'))
  const values = { label, icon: draft.value.icon || '' }
  emit('save', props.item ? values : { ...values, dt: draft.value.dt })
  open.value = false
}

function remove() {
  emit('delete')
  open.value = false
}
</script>
