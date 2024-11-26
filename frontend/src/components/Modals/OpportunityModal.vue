<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-white px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-gray-900">
              {{ __('Create Opportunity') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button v-if="isManager()" variant="ghost" class="w-7" @click="openQuickEntryModal">
              <EditIcon class="h-4 w-4" />
            </Button>
            <Button variant="ghost" class="w-7" @click="show = false">
              <FeatherIcon name="x" class="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div>
          <div class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div class="flex items-center gap-3 text-sm text-gray-600">
              <div>{{ __('Choose Existing Customer') }}</div>
              <Switch v-model="chooseExistingCustomer" />
            </div>
            <div class="flex items-center gap-3 text-sm text-gray-600">
              <div>{{ __('Choose Existing Contact') }}</div>
              <Switch v-model="chooseExistingContact" />
            </div>
          </div>
          <Fields v-if="filteredSections" class="border-t pt-4" :sections="filteredSections" :data="opportunity" />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button variant="solid" :label="__('Create')" :loading="isOpportunityCreating" @click="createOpportunity" />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import Fields from '@/components/Fields.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { capture } from '@/telemetry'
import { Switch, createResource } from 'frappe-ui'
import { computed, ref, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { getUser, isManager } = usersStore()
const { getDealStatus, statusOptions } = statusesStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)

const opportunity = reactive({
  customer: '',
  customer_name: '',
  website: '',
  no_of_employees: '',
  territory: '',
  industry: '',
  contact: '',
  salutation: '',
  first_name: '',
  last_name: '',
  email: '',
  mobile_no: '',
  gender: '',
  status: '',
  opportunity_owner: '',
  lead: '',
  opportunity_amount: '',
})

const isOpportunityCreating = ref(false)
const chooseExistingCustomer = ref(false)
const chooseExistingContact = ref(false)

const sections = createResource({
  url: 'next_crm.ncrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['quickEntryFields', 'Opportunity'],
  params: { doctype: 'Opportunity', type: 'Quick Entry' },
  auto: true,
  transform: (data) => {
    return data.forEach((section) => {
      section.fields.forEach((field) => {
        if (field.name == 'status') {
          field.type = 'Select'
          field.options = opportunityStatuses.value
          field.prefix = getDealStatus(opportunity.status).iconColorClass
        } else if (field.name == 'opportunity_owner') {
          field.type = 'User'
        }
      })
    })
  },
})

const filteredSections = computed(() => {
  let allSections = sections.data || []
  if (!allSections.length) return []

  let _filteredSections = []

  if (chooseExistingCustomer.value) {
    _filteredSections.push(allSections.find((s) => s.label === 'Select Customer'))
  } else {
    _filteredSections.push(allSections.find((s) => s.label === 'Customer Details'))
  }

  if (chooseExistingContact.value) {
    _filteredSections.push(allSections.find((s) => s.label === 'Select Contact'))
  } else {
    _filteredSections.push(allSections.find((s) => s.label === 'Contact Details'))
  }

  allSections.forEach((s) => {
    if (!['Select Customer', 'Customer Details', 'Select Contact', 'Contact Details'].includes(s.label)) {
      _filteredSections.push(s)
    }
  })

  return _filteredSections
})

const opportunityStatuses = computed(() => {
  let statuses = statusOptions('opportunity')
  if (!opportunity.status) {
    opportunity.status = statuses[0].value
  }
  return statuses
})

function createOpportunity() {
  if (opportunity.website && !opportunity.website.startsWith('http')) {
    opportunity.website = 'https://' + opportunity.website
  }
  createResource({
    url: 'next_crm.overrides.opportunity.create_opportunity',
    params: { args: opportunity },
    auto: true,
    validate() {
      error.value = null
      if (opportunity.opportunity_amount) {
        opportunity.opportunity_amount = opportunity.opportunity_amount.replace(/,/g, '')
        if (isNaN(opportunity.opportunity_amount)) {
          error.value = __('Annual Revenue should be a number')
          return error.value
        }
      }
      if (opportunity.contact_mobile && isNaN(opportunity.contact_mobile.replace(/[-+() ]/g, ''))) {
        error.value = __('Mobile No should be a number')
        return error.value
      }
      if (opportunity.contact_email && !opportunity.contact_email.includes('@')) {
        error.value = __('Invalid Email')
        return error.value
      }
      if (!opportunity.status) {
        error.value = __('Status is required')
        return error.value
      }
      isOpportunityCreating.value = true
    },
    onSuccess(name) {
      capture('opportunity_created')
      isOpportunityCreating.value = false
      show.value = false
      router.push({ name: 'Opportunity', params: { opportunityId: name } })
    },
    onError(err) {
      isOpportunityCreating.value = false
      if (!err.messages) {
        error.value = err.message
        return
      }
      error.value = err.messages.join('\n')
    },
  })
}

const showQuickEntryModal = defineModel('quickEntry')

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  nextTick(() => {
    show.value = false
  })
}

onMounted(() => {
  Object.assign(opportunity, props.defaults)
  if (!opportunity.opportunity_owner) {
    opportunity.opportunity_owner = getUser().name
  }
  if (!opportunity.status && opportunityStatuses.value[0].value) {
    opportunity.status = opportunityStatuses.value[0].value
  }
})
</script>
