<template>
  <Dialog
    v-model="show"
    :options="{
      title: editMode
        ? 'Edit View'
        : duplicateMode
        ? 'Duplicate View'
        : 'Create View',
      actions: [
        {
          label: editMode ? 'Save Changes' : duplicateMode ? 'Duplicate' : 'Create',
          variant: 'solid',
          onClick: () => (editMode ? update() : create()),
        },
      ],
    }"
  >
    <template #body-content>
      <FormControl
        variant="outline"
        size="md"
        type="text"
        label="View Name"
        placeholder="View Name"
        v-model="view.label"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog, FormControl, call } from 'frappe-ui'
import { ref, watch, defineModel, nextTick } from 'vue'

const show = defineModel()
const editMode = ref(false)
const duplicateMode = ref(false)
const _view = ref({
  name: '',
  label: '',
  filters: {},
  order_by: 'modified desc',
  columns: '',
  rows: '',
})

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  view: {
    type: Object,
    default: () => {},
  },
  options: {
    type: Object,
    default: {
      afterCreate: () => {},
      afterUpdate: () => {},
    },
  },
})

async function create() {
  props.view.doctype = props.doctype
  let v = await call(
    'crm.fcrm.doctype.crm_view_settings.crm_view_settings.create',
    {
      view: props.view,
      duplicate: duplicateMode.value,
    }
  )
  show.value = false
  props.options.afterCreate?.(v, props.view)
}

async function update() {
  props.view.doctype = props.doctype
  await call('crm.fcrm.doctype.crm_view_settings.crm_view_settings.update', {
    view: props.view,
  })
  show.value = false
  props.options.afterUpdate?.(props.view)
}

watch(show, (value) => {
  if (!value) return
  editMode.value = false
  duplicateMode.value = false
  nextTick(() => {
    _view.value = { ...props.view }
    if (_view.value.name) {
      editMode.value = true
    } else if (_view.value.label) {
      duplicateMode.value = true
    }
  })
})
</script>
