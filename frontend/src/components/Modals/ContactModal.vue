<template>
  <Dialog v-model="dialogShow" :options="{ size: 'xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('New Contact') }}
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
            <Button variant="ghost" class="w-7" @click="handleClose">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <FieldLayout
          v-if="tabs.data"
          :tabs="tabs.data"
          :data="_contact"
          @change="handleFieldChange"
        />
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="loading"
            @click="createContact"
          />
        </div>
      </div>
    </template>
  </Dialog>
  <ConfirmCloseDialog 
    v-model="showConfirmClose"
    @confirm="confirmClose"
    @cancel="cancelClose"
  />
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import ConfirmCloseDialog from '@/components/Modals/ConfirmCloseDialog.vue'
import { usersStore } from '@/stores/users'
import { isMobileView } from '@/composables/settings'
import { capture } from '@/telemetry'
import { call, createResource } from 'frappe-ui'
import { ref, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  contact: {
    type: Object,
    default: () => ({}),
  },
  options: {
    type: Object,
    default: () => ({
      redirect: true,
      afterInsert: () => {},
    }),
  },
  initialValues: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['openAddressModal'])

const { isManager } = usersStore()

const router = useRouter()
const show = defineModel()
const dialogShow = ref(false)
const showConfirmClose = ref(false)

const loading = ref(false)
const isDirty = ref(false)
const tempFormData = ref(null)

let _contact = ref({})

async function createContact() {
  if (_contact.value.email_id) {
    _contact.value.email_ids = [{ email_id: _contact.value.email_id }]
    delete _contact.value.email_id
  }

  if (_contact.value.mobile_no) {
    _contact.value.phone_nos = [{ phone: _contact.value.mobile_no }]
    delete _contact.value.mobile_no
  }

  loading.value = true
  try {
    const doc = await call('frappe.client.insert', {
      doc: {
        doctype: 'Contact',
        ..._contact.value,
      },
    })
    
    if (doc.name) {
      capture('contact_created')
      isDirty.value = false
      handleContactUpdate(doc)
    }
  } finally {
    loading.value = false
  }
}

function handleContactUpdate(doc) {
  props.contact?.reload?.()
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Contact',
      params: { contactId: doc.name },
    })
  }
  isDirty.value = false
  dialogShow.value = false
  show.value = false
  props.options.afterInsert && props.options.afterInsert(doc)
}

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Contact'],
  params: { doctype: 'Contact', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'email_id') {
              field.read_only = false
            } else if (field.fieldname == 'mobile_no') {
              field.read_only = false
            } else if (field.fieldname == 'company_name') {
              field.read_only = false
            } else if (field.fieldname == 'address') {
              field.create = (value, close) => {
                _contact.value.address = value
                emit('openAddressModal')
                dialogShow.value = false
                close()
              }
              field.edit = (address) => {
                emit('openAddressModal', address)
                dialogShow.value = false
              }
            } else if (field.fieldtype === 'Table') {
              _contact.value[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

const showQuickEntryModal = defineModel('showQuickEntryModal')
const shouldOpenLayoutSettings = ref(false)

function openQuickEntryModal() {
  if (isDirty.value) {
    tempFormData.value = { ..._contact.value }
    shouldOpenLayoutSettings.value = true
    showConfirmClose.value = true
  } else {
    dialogShow.value = false
    nextTick(() => {
      showQuickEntryModal.value = true
      show.value = false
    })
  }
}

function handleFieldChange() {
  isDirty.value = true
}

function handleClose() {
  if (isDirty.value) {
    tempFormData.value = { ..._contact.value }
    showConfirmClose.value = true
  } else {
    dialogShow.value = false
    show.value = false
  }
}

function confirmClose() {
  isDirty.value = false
  tempFormData.value = null
  _contact.value = {}
  dialogShow.value = false
  show.value = false
  
  if (shouldOpenLayoutSettings.value) {
    nextTick(() => {
      showQuickEntryModal.value = true
      shouldOpenLayoutSettings.value = false
    })
  }
}

function cancelClose() {
  showConfirmClose.value = false
  shouldOpenLayoutSettings.value = false
  if (tempFormData.value) {
    _contact.value = tempFormData.value
    tempFormData.value = null
  }
}

watch(
  () => dialogShow.value,
  (value) => {
    if (value) return
    if (isDirty.value) {
      showConfirmClose.value = true
      nextTick(() => {
        if (tempFormData.value) {
          _contact.value = tempFormData.value
        }
        dialogShow.value = true
      })
    } else {
      _contact.value = {}
      tempFormData.value = null
      show.value = false
    }
  }
)

watch(
  () => show.value,
  (value) => {
    if (value === dialogShow.value) return
    if (value) {
      isDirty.value = false
      _contact.value = {
        ...props.contact,
        ...props.initialValues,
      }
      dialogShow.value = true
    } else {
      tempFormData.value = null
      dialogShow.value = true
    }
  },
  { immediate: true }
)

watch(
  () => showQuickEntryModal.value,
  (value) => {
    if (!value) {
      tabs.reload()
    }
  }
)
</script>

<style scoped>
:deep(:has(> .dropdown-button)) {
  width: 100%;
}
</style>
