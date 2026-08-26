<template>
  <div class="flex flex-col gap-6" :class="embedded ? '' : 'h-full'">
    <div v-if="!hideHeader" class="flex justify-between">
      <div class="flex flex-col gap-1 w-9/12">
        <div class="flex gap-1 items-center">
          <Button
            v-if="back"
            variant="ghost"
            icon-left="lucide-chevron-left"
            :label="title || __(doctype)"
            size="md"
            class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
            @click="back"
          />
          <h2
            v-else
            class="flex gap-2 text-2xl-semibold leading-none h-5 text-ink-gray-8"
          >
            {{ title || __(doctype) }}
          </h2>
          <Badge
            v-if="isDirty"
            :label="__('Not Saved')"
            variant="subtle"
            theme="orange"
          />
        </div>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <!-- Nothing to save until something changes, so don't offer it — but a
             new record always offers Create, even before the first keystroke. -->
        <Button
          v-if="isDirty || isNew"
          :loading="saving"
          :label="isNew ? __('Create') : __('Save')"
          variant="solid"
          @click="save"
        />
      </div>
    </div>
    <!-- p-1/-m-1 leaves the scroll box a little slack beyond the content, so a
         focused control's ring isn't clipped by the edge it sits flush against.
         `overflow-y-auto` clips horizontally too, which is where it shows. -->
    <div
      v-if="!loading"
      :class="embedded ? '' : 'flex-1 overflow-y-auto p-1 -m-1'"
    >
      <FieldLayout
        v-if="doc && tabs"
        :tabs="tabs"
        :data="doc"
        :doctype="doctype"
        :context="newDocContext"
      />
    </div>
    <div v-else class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="size-8" />
    </div>
    <ErrorMessage :message="error" />
  </div>
</template>
<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import {
  call,
  createDocumentResource,
  createResource,
  LoadingIndicator,
  Badge,
  toast,
  ErrorMessage,
} from 'frappe-ui'
import { getRandom } from '@/utils'
import { computed, onMounted, reactive, ref } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  // Record to load. Defaults to the doctype name so Single DocTypes (the
  // original use) keep working; pass an explicit name to edit one record of
  // a multi-record DocType (e.g. a specific WhatsApp Account).
  name: { type: String, default: '' },
  // Render a blank record that is only created on save, so adding one is the
  // same screen as editing one rather than a dialog first.
  isNew: { type: Boolean, default: false },
  title: { type: String, default: '' },
  successMessage: { type: String, default: 'Updated successfully' },
  back: { type: Function, default: null },
  // When true, drop the full-height/own-scroll layout so the page sizes to its
  // content and can be stacked inside a parent that owns the scroll.
  embedded: { type: Boolean, default: false },
  // When true, skip the title/Update header so a parent can own it. The parent
  // drives saving through the exposed `save`/`isDirty`.
  hideHeader: { type: Boolean, default: false },
  // Fieldnames to leave out of the rendered form, for values the page owns
  // through a purpose-built control elsewhere.
  excludeFields: { type: Array, default: () => [] },
})

const emit = defineEmits(['created'])

const fields = createResource({
  url: 'crm.api.doc.get_fields',
  cache: ['fields', props.doctype],
  params: {
    doctype: props.doctype,
    allow_all_fieldtypes: true,
  },
  auto: true,
})

// Document resources are cached by doctype+name, so this page keeps its unsaved
// edits when it is unmounted and remounted — which Tabs does on every switch.
// `auto` would defeat that: the cache reloads an auto resource on every lookup,
// overwriting the edits. Fetch once instead, only when there is nothing yet.
const data = props.isNew
  ? null
  : createDocumentResource({
      doctype: props.doctype,
      name: props.name || props.doctype,
      fields: ['*'],
      auto: false,
      setValue: {
        onSuccess: () => {
          toast.success(__(props.successMessage))
        },
        onError: (err) => {
          toast.error(err.message + ': ' + err.messages[0])
        },
      },
    })

const newDoc = reactive({})
// A record that does not exist yet has no name, and useDocument() — which is
// where FieldLayout normally gets its change handler — does nothing without one,
// so edits would be dropped. FieldLayout's standalone mode writes straight into
// the bound object instead, which is what an unsaved record needs.
const newDocContext = props.isNew ? { fieldPropertyOverrides: {} } : null
const creating = ref(false)
const createError = ref('')

onMounted(() => {
  if (data && !data.doc) data.get.fetch()
})

const doc = computed(() => (props.isNew ? newDoc : data?.doc))

const loading = computed(() =>
  props.isNew ? false : Boolean(data?.get?.loading) && !data?.doc,
)

const isDirty = computed(() =>
  props.isNew ? Object.keys(newDoc).length > 0 : Boolean(data?.isDirty),
)

const saving = computed(() =>
  props.isNew ? creating.value : Boolean(data?.save?.loading),
)

const error = computed(() =>
  props.isNew ? createError.value : data?.save?.error,
)

async function save() {
  if (!props.isNew) {
    data.save.submit()
    return
  }

  createError.value = ''
  creating.value = true
  try {
    const created = await call('frappe.client.insert', {
      doc: { doctype: props.doctype, ...newDoc },
    })
    toast.success(__(props.successMessage))
    emit('created', created.name)
  } catch (err) {
    createError.value = err.messages?.[0] || err.message
  } finally {
    creating.value = false
  }
}

const tabs = computed(() => {
  if (!fields.data) return []
  let _tabs = []
  let fieldsData = fields.data.filter(
    (field) => !props.excludeFields.includes(field.fieldname),
  )
  if (!fieldsData.length) return []

  if (fieldsData[0].type != 'Tab Break') {
    let _sections = []
    if (fieldsData[0].type != 'Section Break') {
      _sections.push({
        name: 'first_section',
        columns: [{ name: 'first_column', fields: [] }],
      })
    }
    _tabs.push({ name: 'first_tab', sections: _sections })
  }

  fieldsData.forEach((field) => {
    let last_tab = _tabs[_tabs.length - 1]
    let _sections = _tabs.length ? last_tab.sections : []
    if (field.fieldtype === 'Tab Break') {
      _tabs.push({
        label: field.label,
        name: field.fieldname,
        sections: [
          {
            name: 'section_' + getRandom(),
            columns: [{ name: 'column_' + getRandom(), fields: [] }],
          },
        ],
      })
    } else if (field.fieldtype === 'Section Break') {
      _sections.push({
        label: field.label,
        name: field.fieldname,
        hideBorder: field.hide_border,
        columns: [{ name: 'column_' + getRandom(), fields: [] }],
      })
    } else if (field.fieldtype === 'Column Break') {
      _sections[_sections.length - 1].columns.push({
        name: field.fieldname,
        fields: [],
      })
    } else {
      let last_section = _sections[_sections.length - 1]
      let last_column = last_section.columns[last_section.columns.length - 1]
      last_column.fields.push(field)
    }
  })

  // Excluding a field can empty the column it sat in. Columns are flex-1, so an
  // empty one would still hold its share of the row's width.
  _tabs.forEach((tab) =>
    tab.sections.forEach(
      (section) =>
        (section.columns = section.columns.filter(
          (column) => column.fields.length,
        )),
    ),
  )

  return _tabs
})

defineExpose({ isDirty, saving, save })
</script>
