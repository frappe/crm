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
              @click="openQuickEntryModal"
            >
              <EditIcon class="h-4 w-4" />
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div v-if="tabs.data">
          <FieldLayout
            :tabs="tabs.data"
            :data="_callLog"
            doctype="CRM Call Log"
          />
          <ErrorMessage class="mt-2" :message="error" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
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
  <QuickEntryModal
    v-if="showQuickEntryModal"
    v-model="showQuickEntryModal"
    doctype="CRM Call Log"
  />
</template>

<script setup>
import QuickEntryModal from '@/components/Modals/QuickEntryModal.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { getRandom } from '@/utils'
import { capture } from '@/telemetry'
import { FeatherIcon, createResource, ErrorMessage } from 'frappe-ui'
import { ref, nextTick, watch, computed } from 'vue'

const props = defineProps({
  options: {
    type: Object,
    default: {
      afterInsert: () => {},
    },
  },
})

const { isManager } = usersStore()

const show = defineModel()
const callLog = defineModel('callLog')

const loading = ref(false)
const error = ref(null)
const title = ref(null)
const editMode = ref(false)

let _callLog = ref({
  name: '',
  type: '',
  from: '',
  to: '',
  medium: '',
  duration: '',
  caller: '',
  receiver: '',
  status: '',
  recording_url: '',
  telephony_medium: 'Manual',
})

const dialogOptions = computed(() => {
  let title = !editMode.value ? __('New Call Log') : __('Edit Call Log')
  let size = 'xl'
  let actions = [
    {
      label: editMode.value ? __('Save') : __('Create'),
      variant: 'solid',
      onClick: () =>
        editMode.value ? updateCallLog() : createCallLog.submit(),
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

let doc = ref({})

function updateCallLog() {
  error.value = null
  const old = { ...doc.value }
  const newCallLog = { ..._callLog.value }

  const dirty = JSON.stringify(old) !== JSON.stringify(newCallLog)

  if (!dirty) {
    show.value = false
    return
  }

  loading.value = true
  updateCallLogValues.submit({
    doctype: 'CRM Call Log',
    name: _callLog.value.name,
    fieldname: newCallLog,
  })
}

const updateCallLogValues = createResource({
  url: 'frappe.client.set_value',
  onSuccess(doc) {
    loading.value = false
    if (doc.name) {
      handleCallLogUpdate(doc)
    }
  },
  onError(err) {
    loading.value = false
    error.value = err
  },
})

const createCallLog = createResource({
  url: 'frappe.client.insert',
  makeParams() {
    return {
      doc: {
        doctype: 'CRM Call Log',
        id: getRandom(6),
        telephony_medium: 'Manual',
        ..._callLog.value,
      },
    }
  },
  onSuccess(doc) {
    loading.value = false
    if (doc.name) {
      capture('call_log_created')
      handleCallLogUpdate(doc)
    }
  },
  onError(err) {
    loading.value = false
    error.value = err
  },
})

function handleCallLogUpdate(doc) {
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

watch(
  () => show.value,
  (value) => {
    if (!value) return
    editMode.value = false
    nextTick(() => {
      // TODO: Issue with FormControl
      // title.value.el.focus()
      doc.value = callLog.value?.data || {}
      _callLog.value = { ...doc.value }
      if (_callLog.value.name) {
        editMode.value = true
      }
    })
  },
)

const showQuickEntryModal = ref(false)

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => {
    show.value = false
  })
}
</script>
