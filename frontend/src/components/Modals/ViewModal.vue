<template>
  <Dialog
    v-model="show"
    :options="{
      title: editMode
        ? __('Edit View')
        : duplicateMode
          ? __('Duplicate View')
          : __('Create View'),
      actions: [
        {
          label: editMode
            ? __('Save Changes')
            : duplicateMode
              ? __('Duplicate')
              : __('Create'),
          variant: 'solid',
          onClick: () => (editMode ? update() : create()),
        },
      ],
    }"
  >
    <template #body-content>
      <div class="mb-1.5 block text-base text-ink-gray-5">
        {{ __('View Name') }}
      </div>
      <div class="flex gap-2">
        <IconPicker v-model="view.icon" v-slot="{ togglePopover }">
          <Button
            size="md"
            class="flex size-8 text-2xl leading-none"
            :label="view.icon"
            @click="togglePopover"
          />
        </IconPicker>
        <FormControl
          class="flex-1"
          size="md"
          type="text"
          :placeholder="__('My Open Deals')"
          v-model="view.label"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import IconPicker from '@/components/IconPicker.vue'
import { call } from 'frappe-ui'
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  options: {
    type: Object,
    default: {
      afterCreate: () => {},
      afterUpdate: () => {},
    },
  },
})

const show = defineModel()
const view = defineModel('view')

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
