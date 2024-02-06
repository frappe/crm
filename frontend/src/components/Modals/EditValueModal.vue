<template>
  <Dialog v-model="show" :options="{ title: 'Bulk Edit' }">
    <template #body-content>
      <div class="mb-4">
        <div class="mb-1.5 text-sm text-gray-600">Field</div>
        <Autocomplete
          :value="field.label"
          :options="fields.data"
          @change="(e) => changeField(e)"
          placeholder="Select Field..."
        />
      </div>
      <div>
        <div class="mb-1.5 text-sm text-gray-600">Value</div>
        <component
          :is="getValueComponent(field)"
          :value="newValue"
          size="md"
          @change="(v) => updateValue(v)"
          placeholder="Value"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        @click="updateValues"
        :loading="loading"
        :label="`Update ${recordCount} Records`"
      />
    </template>
  </Dialog>
</template>

<script setup>
import DatePicker from '@/components/Controls/DatePicker.vue'
import Link from '@/components/Controls/Link.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { FormControl, call, createResource } from 'frappe-ui'
import { ref, computed, defineModel, onMounted, h } from 'vue'

const typeCheck = ['Check']
const typeLink = ['Link', 'Dynamic Link']
const typeNumber = ['Float', 'Int', 'Currency', 'Percent']
const typeSelect = ['Select']
const typeDate = ['Date', 'Datetime']

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  selectedValues: {
    type: Array,
    required: true,
  },
})

const show = defineModel()
const unselectAll = defineModel('unselectAll')

const emit = defineEmits(['reload'])

const fields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', props.doctype],
  params: {
    doctype: props.doctype,
  },
})

onMounted(() => {
  if (fields.data?.length) return
  fields.fetch()
})

const recordCount = computed(() => props.selectedValues?.size || 0)

const field = ref({
  label: '',
  type: '',
  value: '',
  options: '',
})

const newValue = ref('')
const loading = ref(false)

function updateValues() {
  let fieldVal = newValue.value
  if (field.value.type == 'Check') {
    fieldVal = fieldVal == 'Yes' ? 1 : 0
  }
  loading.value = true
  call(
    'frappe.desk.doctype.bulk_update.bulk_update.submit_cancel_or_update_docs',
    {
      doctype: props.doctype,
      docnames: Array.from(props.selectedValues),
      action: 'update',
      data: {
        [field.value.value]: fieldVal || null,
      },
    }
  ).then(() => {
    field.value = {
      label: '',
      type: '',
      value: '',
      options: '',
    }
    newValue.value = ''
    loading.value = false
    show.value = false
    unselectAll.value()
    emit('reload')
  })
}

function changeField(f) {
  newValue.value = ''
  if (!f) return
  field.value = f
}

function updateValue(v) {
  let value = v.target ? v.target.value : v
  newValue.value = value
}

function getValueComponent(f) {
  const { type, options } = f
  if (typeSelect.includes(type) || typeCheck.includes(type)) {
    const _options = type == 'Check' ? ['Yes', 'No'] : getSelectOptions(options)
    return h(FormControl, {
      type: 'select',
      options: _options.map((o) => ({
        label: o,
        value: o,
      })),
    })
  } else if (typeLink.includes(type)) {
    if (type == 'Dynamic Link') {
      return h(FormControl, { type: 'text' })
    }
    return h(Link, { class: 'form-control', doctype: options })
  } else if (typeNumber.includes(type)) {
    return h(FormControl, { type: 'number' })
  } else if (typeDate.includes(type)) {
    return h(DatePicker)
  } else {
    return h(FormControl, { type: 'text' })
  }
}
</script>
