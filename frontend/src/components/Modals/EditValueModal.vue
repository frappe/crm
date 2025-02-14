<template>
  <Dialog v-model="show" :options="{ title: __('Bulk Edit') }">
    <template #body-content>
      <div class="mb-4">
        <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Field') }}</div>
        <Autocomplete
          :value="field.label"
          :options="fields.data"
          @change="(e) => changeField(e)"
          :placeholder="__('Source')"
        />
      </div>
      <div>
        <div class="mb-1.5 text-sm text-ink-gray-5">{{ __('Value') }}</div>
        <component
          :is="getValueComponent(field)"
          :value="newValue"
          size="md"
          @change="(v) => updateValue(v)"
          :placeholder="__('Contact Us')"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        @click="updateValues"
        :loading="loading"
        :label="__('Update {0} Records', [recordCount])"
      />
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { capture } from '@/telemetry'
import { FormControl, call, createResource, TextEditor } from 'frappe-ui'
import { ref, computed, onMounted, h } from 'vue'
import { translateLeadStatus } from '@/utils/leadStatusTranslations'
import { translateDealStatus } from '@/utils/dealStatusTranslations'
import { translateTaskStatus } from '@/utils/taskStatusTranslations'
import { translateTaskPriority } from '@/utils/taskPriorityTranslations'

const typeCheck = ['Check']
const typeLink = ['Link', 'Dynamic Link']
const typeNumber = ['Float', 'Int', 'Currency', 'Percent']
const typeSelect = ['Select']
const typeEditor = ['Text Editor']
const typeDate = ['Date', 'Datetime']

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  selectedValues: {
    type: Set,
    required: true,
  },
})

const show = defineModel()

const emit = defineEmits(['reload'])

const fields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', props.doctype],
  params: {
    doctype: props.doctype,
  },
  transform: (data) => {
    return data
      .filter((f) => f.hidden == 0 && f.read_only == 0)
      .map(f => ({
        ...f,
        label: __(f.label)
      }))
  }
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
    fieldVal = fieldVal == __('Yes') ? 1 : 0
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
    capture('bulk_update', { doctype: props.doctype })
    emit('reload')
  })
}

function changeField(f) {
  newValue.value = ''
  if (!f) return
  
  field.value = {
    label: f.label,
    type: f.fieldtype,
    value: f.fieldname,
    options: f.options || '',
  }
}

function updateValue(v) {
  let value = v.target ? v.target.value : v
  newValue.value = value
}

function getSelectOptions(options) {
  if (!options) return []
  return options.split('\n')
}

function getValueComponent(f) {
  const { type, options, value: fieldname } = f
  
  // Special handling for status and priority fields
  const isStatus = fieldname === 'status'
  const isPriority = fieldname === 'priority'

  if ((isStatus || isPriority) && (type === 'Link' || type === 'Select')) {
    let _options = []
    let translateFn = null

    if (props.doctype === 'CRM Deal') {
      _options = ['Proposal/Quotation', 'Ready to Close', 'Demo/Making', 'Qualification', 'Negotiation', 'Won', 'Lost']
      translateFn = translateDealStatus
    } else if (props.doctype === 'CRM Lead') {
      _options = ['New', 'Working', 'Replied', 'Open', 'Opportunity', 'Interested', 'Quotation', 'Lost', 'Converted', 'Do Not Contact Again']
      translateFn = translateLeadStatus
    } else if (props.doctype === 'CRM Task') {
      if (isStatus) {
        _options = ['Backlog', 'Todo', 'In Progress', 'Done', 'Canceled']
        translateFn = translateTaskStatus
      } else if (isPriority) {
        _options = ['Low', 'Medium', 'High']
        translateFn = translateTaskPriority
      }
    }

    if (_options.length && translateFn) {
      const translatedOptions = _options.map((o) => ({
        label: translateFn(o),
        value: o,
      }))

      return h(FormControl, {
        type: 'select',
        options: translatedOptions,
        value: newValue.value,
        onChange: (e) => updateValue(e)
      })
    }
  }

  if (typeSelect.includes(type) || typeCheck.includes(type)) {
    const _options = type == 'Check' ? ['Yes', 'No'] : getSelectOptions(options)
    return h(FormControl, {
      type: 'select',
      options: _options.map((o) => ({
        label: __(o),
        value: o,
      })),
      value: newValue.value,
      onChange: (e) => updateValue(e)
    })
  } else if (typeLink.includes(type)) {
    if (type == 'Dynamic Link') {
      return h(FormControl, { type: 'text' })
    }
    return h(Link, { 
      class: 'form-control', 
      doctype: options,
      value: newValue.value,
      onChange: (v) => updateValue(v)
    })
  } else if (typeNumber.includes(type)) {
    return h(FormControl, { 
      type: 'number',
      value: newValue.value,
      onChange: (e) => updateValue(e)
    })
  } else if (typeDate.includes(type)) {
    return h('input', {
      type: type === 'Date' ? 'date' : 'datetime-local',
      value: newValue.value,
      class: 'w-full rounded border border-gray-100 bg-surface-gray-2 px-2 py-1.5 text-base text-ink-gray-8 placeholder-ink-gray-4 transition-colors hover:border-outline-gray-modals hover:bg-surface-gray-3 focus:border-outline-gray-4 focus:bg-surface-white focus:shadow-sm focus:outline-none focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3',
      onInput: (e) => updateValue(e)
    })
  } else if (typeEditor.includes(type)) {
    return h(TextEditor, {
      variant: 'outline',
      editorClass:
        '!prose-sm overflow-auto min-h-[80px] max-h-80 py-1.5 px-2 rounded border border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors',
      bubbleMenu: true,
      content: newValue.value,
      onInput: (v) => updateValue(v)
    })
  } else {
    return h(FormControl, { 
      type: 'text',
      value: newValue.value,
      onChange: (e) => updateValue(e)
    })
  }
}
</script>
