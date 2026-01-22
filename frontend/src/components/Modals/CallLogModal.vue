<template>
  <Dialog v-model="show" :options="dialogOptions">
    <template #body>
      <div class="px-4 pt-5 pb-6 bg-surface-modal sm:px-6">
        <div class="flex items-center justify-between mb-5">
          <div class="flex items-center gap-2">
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __(dialogOptions.title) || __('Untitled') }}
            </h3>
            <Badge v-if="callLog.isDirty" :label="'Not Saved'" theme="orange" />
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              :tooltip="__('Edit fields layout')"
              :icon="EditIcon"
              class="w-7"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              @click="show = false"
              icon="x"
            />
          </div>
        </div>
        <div v-if="tabs.data">
          <FieldLayout
            :tabs="tabs.data"
            :data="callLog.doc"
            doctype="CRM Call Log"
          />
          <ErrorMessage class="mt-8" :message="error" />
        </div>
      </div>
      <div class="px-4 pt-4 pb-7 sm:px-6">
        <div class="flex justify-end gap-2">
          <Button
            class="w-full"
            v-for="action in dialogOptions.actions"
            :key="action.label"
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
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { getRandom } from '@/utils'
import { capture } from '@/telemetry'
import { useDocument } from '@/data/document'
import { createResource, ErrorMessage, Badge } from 'frappe-ui'
import { ref, nextTick, computed, onMounted } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({}),
  },
  referenceDoc: {
    type: Object,
    default: () => ({}),
  },
  options: {
    type: Object,
    default: {
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const show = defineModel()

const loading = ref(false)
const error = ref(null)
const editMode = ref(false)

const { document: callLog, triggerOnBeforeCreate } = useDocument(
  'CRM Call Log',
  props.data?.name || '',
)

const dialogOptions = computed(() => {
  let title = !editMode.value ? __('Log a call') : __('Edit call log')
  let size = 'xl'
  let actions = [
    {
      label: editMode.value ? __('Save') : __('Create'),
      variant: 'solid',
      onClick: () => (editMode.value ? updateCallLog() : createCallLog()),
    },
  ]

  return { title, size, actions }
})

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Call Log'],
  params: { doctype: 'CRM Call Log', type: 'Quick Entry' },
  auto: true,
})

const callBacks = {
  onSuccess: (doc) => {
    loading.value = false
    handleCallLogUpdate(doc)
  },
  onError: (err) => {
    loading.value = false
    if (err.exc_type == 'MandatoryError') {
      const errorMessage = err.messages
        .map((msg) => {
          let arr = msg.split(': ')
          return arr[arr.length - 1].trim()
        })
        .join(', ')
      error.value = __('These fields are required: {0}', [errorMessage])
      return
    }
    error.value = err
  },
}

async function updateCallLog() {
  loading.value = true
  await callLog.save.submit(null, callBacks)
}

async function createCallLog() {
  Object.assign(callLog.doc, {
    doctype: 'CRM Call Log',
    id: getRandom(6),
    telephony_medium: 'Manual',
  })

  await triggerOnBeforeCreate?.(props.referenceDoc)
  await _createCallLog.submit({
    doc: callLog.doc,
  })
}

const _createCallLog = createResource({
  url: 'frappe.client.insert',
  onSuccess(doc) {
    loading.value = false
    if (doc.name) {
      capture('call_log_created')
      handleCallLogUpdate(doc)
    }
  },
  onError(err) {
    callBacks.onError(err)
  },
})

function handleCallLogUpdate(doc) {
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

onMounted(() => {
  editMode.value = props.data?.name ? true : false

  if (!props.data?.name) {
    callLog.doc = { ...props.data }
  }
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Call Log' }
  nextTick(() => (show.value = false))
}
</script>
