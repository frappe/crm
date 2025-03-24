<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Rename'),
      size: 'md',
      actions: [
        {
          label: __('Rename'),
          variant: 'solid',
          onClick: renameDoc,
        },
      ],
    }"
  >
    <template #body-content>
      <div>
        <FormControl
          :type="'text'"
          size="md"
          variant="subtle"
          :disabled="false"
          label="New Title"
          v-model="_name.title"
        />
      </div>
      <div class="mt-6">
        <FormControl
          :type="'text'"
          size="md"
          variant="subtle"
          :disabled="false"
          label="New Name"
          v-model="_name.name"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { createToast } from '@/utils'
import { call } from 'frappe-ui'

const props = defineProps({
  title: {
    type: String,
    default: '',
  },
  doctype: {
    type: String,
    default: 'Opportunity',
  },
  docname: {
    type: String,
    default: '',
  },
  options: {
    type: Object,
    default: {
      afterRename: () => {},
    },
  },
})

const _name = ref({
  title: '',
  name: '',
})

const show = defineModel()

async function renameDoc() {
  if (props.title === _name.value.title && props.docname === _name.value.name) return
  try {
    const renamed_docname = await call('frappe.model.rename_doc.update_document_title', {
      doctype: props.doctype,
      docname: props.docname,
      title: _name.value.title,
      name: _name.value.name,
    })
    show.value = false
    createToast({
      title: __(`${props.doctype} Renamed`),
      icon: 'check',
      iconClasses: 'text-ink-green-4',
    })
    props.options.afterRename && props.options.afterRename(renamed_docname)
  } catch (error) {
    createToast({
      title: __('Error'),
      text: error,
      icon: 'x',
      iconClasses: 'text-ink-red-4',
    })
  }
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    nextTick(() => {
      _name.value.title = props.title
      _name.value.name = props.docname
    })
  },
)
</script>
