<template>
  <div class="flex flex-col gap-4">
    <div class="flex flex-col gap-1">
      <span class="text-base-medium text-ink-gray-8">
        {{ __('Subject') }}
      </span>
      <span class="text-p-sm text-ink-gray-6">
        {{
          __(
            'Default subject for new emails. You can still change it before sending.',
          )
        }}
      </span>
    </div>

    <div v-for="dt in doctypes" :key="dt.doctype" class="flex flex-col gap-1.5">
      <label :for="inputId(dt.doctype)" class="text-xs text-ink-gray-5">
        {{ dt.label }}
      </label>
      <div class="flex items-center gap-2">
        <FormControl
          :id="inputId(dt.doctype)"
          :model-value="subject(dt.doctype)"
          class="flex-1"
          type="text"
          :placeholder="defaultEmailSubjects[dt.doctype]"
          @update:model-value="(value) => setSubject(dt.doctype, value)"
          @blur="(e) => saveCaret(dt.doctype, e)"
        />
        <Combobox
          :model-value="null"
          :options="fieldOptions(dt.doctype)"
          align="end"
          @update:selected-option="
            (field) => insertField(dt.doctype, field?.value)
          "
        >
          <template #trigger="{ open, setOpen }">
            <Button
              class="!bg-surface-elevation-2"
              variant="outline"
              :label="__('Add field')"
              iconLeft="lucide-plus"
              @click="setOpen(!open)"
            />
          </template>
          <template #item-label="{ item }">
            <div class="flex items-baseline gap-2 max-w-64">
              <span class="text-ink-gray-8 truncate">{{ item.label }}</span>
              <span class="text-ink-gray-4 text-sm truncate">
                {{ item.value }}
              </span>
            </div>
          </template>
        </Combobox>
      </div>
      <div class="flex gap-1.5 text-p-sm min-w-0">
        <span class="text-ink-gray-5 shrink-0">{{ __('Preview:') }}</span>
        <span class="text-ink-gray-7 truncate">
          {{ renderEmailSubject(subject(dt.doctype), previewDoc(dt.doctype)) }}
        </span>
      </div>
    </div>
  </div>
</template>
<script setup>
import {
  defaultEmailSubjects,
  emailSubjectFields,
  renderEmailSubject,
} from '@/composables/emailSubject'
import { getMeta } from '@/stores/meta'
import { Button, Combobox, FormControl, createResource } from 'frappe-ui'
import { nextTick, reactive } from 'vue'

const props = defineProps({
  doc: { type: Object, required: true },
})

const emit = defineEmits(['change'])

const doctypes = [
  { doctype: 'CRM Lead', label: __('Lead'), idLabel: __('Lead ID') },
  { doctype: 'CRM Deal', label: __('Deal'), idLabel: __('Deal ID') },
]

const inputId = (doctype) =>
  `email-subject-${doctype.toLowerCase().replace(' ', '-')}`

// Show the default until edited, then keep what was typed (even empty)
const edited = reactive({})

function subject(doctype) {
  if (doctype in edited) return edited[doctype]
  return props.doc[emailSubjectFields[doctype]] || defaultEmailSubjects[doctype]
}

function setSubject(doctype, value) {
  edited[doctype] = value
  emit('change', emailSubjectFields[doctype], value)
}

// Field types that don't read as plain text in a subject line
const skipFieldTypes = [
  'Attach',
  'Attach Image',
  'Check',
  'Code',
  'HTML',
  'HTML Editor',
  'JSON',
  'Long Text',
  'Markdown Editor',
  'Password',
  'Signature',
  'Text Editor',
]

const metas = {
  'CRM Lead': getMeta('CRM Lead'),
  'CRM Deal': getMeta('CRM Deal'),
}

function fieldOptions(doctype) {
  return metas[doctype]
    .getFields({ withStandardFields: true })
    .filter((f) => f.label && !skipFieldTypes.includes(f.fieldtype))
    .filter(
      (f) => !['_assign', '_liked_by', 'naming_series'].includes(f.fieldname),
    )
    .map((f) => ({ label: __(f.label), value: f.fieldname }))
}

// Preview against the most recently updated lead or deal
const latest = {}
for (const { doctype } of doctypes) {
  latest[doctype] = createResource({
    url: 'frappe.client.get_list',
    params: {
      doctype,
      fields: ['*'],
      order_by: 'modified desc',
      limit_page_length: 1,
    },
    auto: true,
  })
}

// With no records yet, fill each field with its label, e.g. "[Organization]"
function sampleDoc(doctype) {
  const doc = {}
  for (const f of metas[doctype].getFields({ withStandardFields: true })) {
    doc[f.fieldname] = `[${__(f.label)}]`
  }
  doc.name = `[${doctypes.find((d) => d.doctype === doctype).idLabel}]`
  return doc
}

function previewDoc(doctype) {
  return latest[doctype].data?.[0] || sampleDoc(doctype)
}

const carets = {}

function saveCaret(doctype, e) {
  if (e?.target)
    carets[doctype] = [e.target.selectionStart, e.target.selectionEnd]
}

function insertField(doctype, fieldname) {
  if (!fieldname) return
  const token = `{{ ${fieldname} }}`
  const value = subject(doctype)

  // Insert where the caret was before the picker took focus, else append
  const [start, end] = carets[doctype] || [value.length, value.length]
  const before = value.slice(0, start)
  const after = value.slice(end)
  const pad = before && !before.endsWith(' ') ? ' ' : ''
  setSubject(doctype, `${before}${pad}${token}${after}`)

  const position = before.length + pad.length + token.length
  carets[doctype] = [position, position]
  nextTick(() => {
    const input = document.getElementById(inputId(doctype))
    input?.focus()
    input?.setSelectionRange(position, position)
  })
}
</script>
