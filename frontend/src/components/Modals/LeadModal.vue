<template>
  <Dialog v-model="dialogShow" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Lead') }}
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
        <div>
          <FieldLayout v-if="tabs.data"
          :tabs="tabs.data"
          :data="lead"
          @change="handleFieldChange" />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isLeadCreating"
            @click="createNewLead"
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
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import ConfirmCloseDialog from '@/components/Modals/ConfirmCloseDialog.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { isMobileView } from '@/composables/settings'
import { capture } from '@/telemetry'
import { createResource } from 'frappe-ui'
import { computed, onMounted, ref, reactive, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { getUser, isManager } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()

const show = defineModel()
const dialogShow = ref(false)
const showConfirmClose = ref(false)

const router = useRouter()
const error = ref(null)
const isLeadCreating = ref(false)
const isDirty = ref(false)

const tabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Lead'],
  params: { doctype: 'CRM Lead', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = leadStatuses.value
              field.prefix = getLeadStatus(lead.status).color
            }

            if (field.fieldtype === 'Table') {
              lead[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

const lead = reactive({
  salutation: '',
  first_name: '',
  last_name: '',
  email: '',
  mobile_no: '',
  gender: '',
  organization: '',
  website: '',
  no_of_employees: '',
  territory: '',
  annual_revenue: '',
  industry: '',
  status: '',
  lead_owner: '',
})

const createLead = createResource({
  url: 'frappe.client.insert',
  makeParams(values) {
    return {
      doc: {
        doctype: 'CRM Lead',
        ...values,
      },
    }
  },
})

const leadStatuses = computed(() => {
  let statuses = statusOptions('lead')
  if (!lead.status) {
    lead.status = statuses[0].value
  }
  return statuses
})

function createNewLead() {
  if (lead.website && !lead.website.startsWith('http')) {
    lead.website = 'https://' + lead.website
  }

  createLead.submit(lead, {
    validate() {
      error.value = null
      if (!lead.first_name) {
        error.value = __('First Name is mandatory')
        return error.value
      }
      if (lead.annual_revenue) {
        if (typeof lead.annual_revenue === 'string') {
          lead.annual_revenue = lead.annual_revenue.replace(/,/g, '')
        } else if (isNaN(lead.annual_revenue)) {
          error.value = __('Annual Revenue should be a number')
          return error.value
        }
      }
      if (lead.mobile_no && isNaN(lead.mobile_no.replace(/[-+() ]/g, ''))) {
        error.value = __('Mobile No should be a number')
        return error.value
      }
      if (lead.email && !lead.email.includes('@')) {
        error.value = __('Invalid Email')
        return error.value
      }
      if (!lead.status) {
        error.value = __('Status is required')
        return error.value
      }
      isLeadCreating.value = true
    },
    onSuccess(data) {
      capture('lead_created')
      isLeadCreating.value = false
      show.value = false
      router.push({ name: 'Lead', params: { leadId: data.name } })
    },
    onError(err) {
      isLeadCreating.value = false
      if (!err.messages) {
        error.value = err.message
        return
      }
      error.value = err.messages.join('\n')
    },
  })
}

const showQuickEntryModal = defineModel('quickEntry')
const shouldOpenLayoutSettings = ref(false)

function openQuickEntryModal() {
  if (isDirty.value) {
    shouldOpenLayoutSettings.value = true
    showConfirmClose.value = true
  } else {
    showQuickEntryModal.value = true
    nextTick(() => {
      dialogShow.value = false
      show.value = false
    })
  }
}

function handleFieldChange() {
  isDirty.value = true
}

function handleClose() {
  if (isDirty.value) {
    showConfirmClose.value = true
  } else {
    dialogShow.value = false
    show.value = false
  }
}

function confirmClose() {
  isDirty.value = false
  dialogShow.value = false
  show.value = false
  
  if (shouldOpenLayoutSettings.value) {
    showQuickEntryModal.value = true
    nextTick(() => {
      shouldOpenLayoutSettings.value = false
    })
  }
}

function cancelClose() {
  showConfirmClose.value = false
  shouldOpenLayoutSettings.value = false
}

watch(
  () => dialogShow.value,
  (value) => {
    if (value) return
    if (isDirty.value) {
      showConfirmClose.value = true
      nextTick(() => {
        dialogShow.value = true
      })
    } else {
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
      dialogShow.value = true
    } else {
      dialogShow.value = true
    }
  },
  { immediate: true }
)

onMounted(() => {
  Object.assign(lead, props.defaults)
  if (!lead.lead_owner) {
    lead.lead_owner = getUser().name
  }
  if (!lead.status && leadStatuses.value[0].value) {
    lead.status = leadStatuses.value[0].value
  }
})
</script>
