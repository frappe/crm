<template>
  <Dialog v-model="show" :options="dialogOptions">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __(dialogOptions.title) || __('Untitled') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit Fields Layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              icon="x"
              @click="show = false"
            />
          </div>
        </div>
        <div v-if="tabs.data">
          <FieldLayout :tabs="tabs.data" :data="_data.doc" :doctype="doctype" />
          <ErrorMessage class="mt-2" :message="error" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            v-for="action in dialogOptions.actions"
            :key="action.label"
            class="w-full"
            v-bind="action"
            :label="__(action.label)"
            :loading="loading"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { getMeta } from '@/stores/meta'
import { useDocument } from '@/data/document'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { createResource, ErrorMessage, call } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'

const props = defineProps({
  doctype: { type: String, required: true },
  data: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['callback'])

const { isManager } = usersStore()

const show = defineModel({ type: Boolean })

const loading = ref(false)
const error = ref(null)

const { document: _data, triggerOnBeforeCreate } = useDocument(props.doctype)
const { doctypeMeta } = getMeta(props.doctype)

const dialogOptions = computed(() => {
  let doctype = props.doctype

  if (doctype.startsWith('CRM ') || doctype.startsWith('FCRM ')) {
    doctype = doctype.replace(/^(CRM |FCRM )/, '')
  }

  let title = __('New {0}', [doctype])
  let size = 'xl'
  let actions = [
    {
      label: __('Create'),
      variant: 'solid',
      onClick: () => create(),
    },
  ]

  return { title, size, actions }
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', props.doctype],
  params: { doctype: props.doctype, type: 'Quick Entry' },
  auto: true,
})

watch(
  [tabs, doctypeMeta],
  () => {
    if (!tabs.data || !doctypeMeta.value) return

    if (doctypeMeta.value?.autoname?.toLowerCase() === 'prompt') {
      let hasNewNameField = tabs.data.some((tab) =>
        tab.sections.some((section) =>
          section.columns.some((column) =>
            column.fields.some((field) => field.fieldname === '__newname'),
          ),
        ),
      )

      if (!hasNewNameField) {
        tabs.data[0].sections[0].columns[0].fields.unshift({
          fieldname: '__newname',
          label: __('Name'),
          fieldtype: 'Data',
          reqd: 1,
        })
      }
    }
  },
  { immediate: true, deep: true },
)

async function create() {
  loading.value = true
  error.value = null

  await triggerOnBeforeCreate?.()

  let doc = await call(
    'frappe.client.insert',
    {
      doc: {
        doctype: props.doctype,
        ..._data.doc,
      },
    },
    {
      onError: (err) => {
        loading.value = false
        if (err.error) {
          error.value = err.error.messages?.[0]
        }
      },
    },
  )

  loading.value = false
  show.value = false
  emit('callback', doc)
  _data.doc = {}
}

watch(
  doctypeMeta,
  (meta) => {
    if (!meta) return

    let doc = {}

    if (typeof props.data === 'object') {
      Object.assign(doc, props.data)
    } else if (meta.autoname && meta.autoname.indexOf('field:') !== -1) {
      doc[meta.autoname.substr(6)] = props.data
    } else if (meta.autoname && meta.autoname === 'prompt') {
      doc.__newname = props.data
    } else if (meta.title_field) {
      doc[meta.title_field] = props.data
    }

    nextTick(() => Object.assign(_data.doc, doc))
  },
  { immediate: true, deep: true },
)

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: props.doctype }
  nextTick(() => (show.value = false))
}
</script>
