<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
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
        <div>
          <FieldLayout v-if="tabs.data" :tabs="tabs.data" :data="lead.doc" />
          <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
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
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { sessionStore } from '@/stores/session'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { createResource, toast } from 'frappe-ui'
import { useDocument } from '@/data/document'
import { computed, onMounted, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  defaults: { type: Object, default: () => ({}) },
})

const { user } = sessionStore()
const { getUser, isManager } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show = defineModel({ type: Boolean })
const error = ref(null)
const isLeadCreating = ref(false)

const { document: lead, triggerOnBeforeCreate } = useDocument('CRM Lead')

const { capture } = useTelemetry()

const leadStatuses = computed(() => statusOptions('lead'))

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
              field.prefix = getLeadStatus(lead.doc.status).color
            }

            if (field.fieldtype === 'Table') {
              lead.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

const createLead = createResource({
  url: 'crm.api.lead.create_lead',
})

async function createNewLead() {
  if (lead.doc.website && !lead.doc.website.startsWith('http')) {
    lead.doc.website = 'https://' + lead.doc.website
  }

  await triggerOnBeforeCreate?.()

  error.value = null
  if (!lead.doc.first_name) {
    error.value = __('First Name is mandatory')
    return
  }
  if (lead.doc.annual_revenue) {
    if (typeof lead.doc.annual_revenue === 'string') {
      lead.doc.annual_revenue = lead.doc.annual_revenue.replace(/,/g, '')
    } else if (isNaN(lead.doc.annual_revenue)) {
      error.value = __('Annual Revenue should be a number')
      return
    }
  }
  if (lead.doc.mobile_no && isNaN(lead.doc.mobile_no.replace(/[-+() ]/g, ''))) {
    error.value = __('Mobile No. should be a number')
    return
  }
  if (lead.doc.email && !lead.doc.email.includes('@')) {
    error.value = __('Invalid email address')
    return
  }
  if (!lead.doc.status) {
    error.value = __('Status is required')
    return
  }

  isLeadCreating.value = true
  try {
    const data = await createLead.submit({
      doc: {
        doctype: 'CRM Lead',
        ...lead.doc,
      },
    })

    capture('lead_created')
    isLeadCreating.value = false
    router.push({ name: 'Lead', params: { leadId: data.name } })
    show.value = false
    lead.doc = {}
    updateOnboardingStep('create_first_lead', true, false, () => {
      localStorage.setItem('firstLead' + user, data.name)
    })
    if (data.duplicate_warning && data.possible_duplicates?.length) {
      const names = data.possible_duplicates
        .map((d) => d.lead_name || d.name)
        .join(', ')
      toast.warning(__('Possible duplicate with: {0}', [names]))
    }
  } catch (err) {
    isLeadCreating.value = false
    if (!err.messages) {
      error.value = err.message
      return
    }
    error.value = err.messages.join('\n')
  }
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Lead' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  lead.doc.no_of_employees = '1-10'
  Object.assign(lead.doc, props.defaults)

  if (!lead.doc?.lead_owner) {
    lead.doc.lead_owner = getUser().name
  }
  if (!lead.doc?.status && leadStatuses.value[0]?.value) {
    lead.doc.status = leadStatuses.value[0].value
  }
})
</script>
