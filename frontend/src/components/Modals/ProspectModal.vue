<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Prospect') }}
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
          <Fields v-if="sections.data" :sections="sections.data" :data="prospect" />
          <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button variant="solid" :label="__('Create')" :loading="isProspectCreating" @click="createNewProspect" />
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
import { createResource } from 'frappe-ui'
import { computed, onMounted, ref, reactive, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { getUser, isManager } = usersStore()
const { statusOptions } = statusesStore()

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isProspectCreating = ref(false)

const sections = createResource({
  url: 'next_crm.ncrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['quickEntryFields', 'Prospect'],
  params: { doctype: 'Prospect', type: 'Quick Entry' },
  auto: true,
  transform: (data) => {
    return data.forEach((section) => {
      section.fields.forEach((field) => {
        if (field.name == 'prospect_owner') {
          field.type = 'User'
        }
      })
    })
  },
})

const prospect = reactive({
  company_name: '',
  market_segment: '',
  prospect_owner: '',
  customer_group: '',
  industry: '',
  no_of_employees: '',
  website: '',
  no_of_employees: '',
  territory: '',
  annual_revenue: '',
  prospect_owner: '',
})

const createProspect = createResource({
  url: 'frappe.client.insert',
  makeParams(values) {
    return {
      doc: {
        doctype: 'Prospect',
        ...values,
      },
    }
  },
})

const prospectStatuses = computed(() => {
  let statuses = statusOptions('prospect')
  if (!prospect.status) {
    prospect.status = statuses[0].value
  }
  return statuses
})

function createNewProspect() {
  if (prospect.website && !prospect.website.startsWith('http')) {
    prospect.website = 'https://' + prospect.website
  }

  createProspect.submit(prospect, {
    validate() {
      error.value = null
      if (!prospect.company_name) {
        error.value = __('Company Name is mandatory')
        return error.value
      }
      if (prospect.annual_revenue) {
        prospect.annual_revenue = prospect.annual_revenue.replace(/,/g, '')
        if (isNaN(prospect.annual_revenue)) {
          error.value = __('Annual Revenue should be a number')
          return error.value
        }
      }
      if (prospect.fax && isNaN(prospect.fax.replace(/[-+() ]/g, ''))) {
        error.value = __('Mobile No should be a number')
        return error.value
      }
      if (prospect.email_id && !prospect.email_id.includes('@')) {
        error.value = __('Invalid Email')
        return error.value
      }
      isProspectCreating.value = true
    },
    onSuccess(data) {
      capture('prospect_created')
      isProspectCreating.value = false
      show.value = false
      router.push({ name: 'Prospect', params: { prospectId: data.name } })
    },
    onError(err) {
      isProspectCreating.value = false
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
  Object.assign(prospect, props.defaults)
  if (!prospect.prospect_owner) {
    prospect.prospect_owner = getUser().name
  }
  if (!prospect.status && prospectStatuses.value[0].value) {
    prospect.status = prospectStatuses.value[0].value
  }
})
</script>
