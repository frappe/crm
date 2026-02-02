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
              :tooltip="__('Edit fields layout')"
              :icon="EditIcon"
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
        <div>
          <FieldLayout v-if="currentTabs" :tabs="currentTabs" :data="lead.doc" />
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
          <Button
            v-if="isCRMManager()"
            :variant="formMode === 'long' ? 'solid' : 'outline'"
            :label="__('Long Form')"
            @click="formMode = 'long'"
          />
          <Button
            v-if="isCRMManager()"
            :variant="formMode === 'short' ? 'solid' : 'outline'"
            :label="__('Short Form')"
            @click="formMode = 'short'"
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
import { capture } from '@/telemetry'
import { createResource } from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { useDocument } from '@/data/document'
import { computed, onMounted, ref, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: Object,
})

const { user } = sessionStore()
const { getUser, isManager, isCRMManager } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show = defineModel()
const router = useRouter()
const error = ref(null)
const isLeadCreating = ref(false)
const formMode = ref('short') // 'short' for Quick Entry, 'long' for Long Form

const { document: lead, triggerOnBeforeCreate } = useDocument('CRM Lead')

const leadStatuses = computed(() => {
  let statuses = statusOptions('lead')
  if (!lead.doc.status) {
    lead.doc.status = statuses?.[0]?.value
  }
  return statuses
})

function transformTabs(_tabs) {
  _tabs.forEach((tab) => {
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
  return _tabs
}

const shortFormTabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'CRM Lead'],
  params: { doctype: 'CRM Lead', type: 'Quick Entry' },
  auto: true,
  transform: transformTabs,
})

const longFormTabs = createResource({
  url: 'singhania_customizations.singhania_customizations.api.get_crm_lead_long_form_layout',
  cache: ['LongForm', 'CRM Lead'],
  auto: true,
  transform: transformTabs,
})

const currentTabs = computed(() => {
  if (formMode.value === 'long') {
    return longFormTabs.data || shortFormTabs.data
  }
  return shortFormTabs.data
})

const createLead = createResource({
  url: 'frappe.client.insert',
})

async function createNewLead() {
  if (lead.doc.website && !lead.doc.website.startsWith('http')) {
    lead.doc.website = 'https://' + lead.doc.website
  }

  await triggerOnBeforeCreate?.()

  createLead.submit(
    {
      doc: {
        doctype: 'CRM Lead',
        ...lead.doc,
      },
    },
    {
      validate() {
        error.value = null
        
        // Common validations for both forms
        if (!lead.doc.first_name) {
          error.value = __('First Name is mandatory')
          return error.value
        }
        
        // For short form, status is still required
        if (formMode.value === 'short' && !lead.doc.status) {
          error.value = __('Status is required')
          return error.value
        }
        
        // Long form specific mandatory validations
        if (formMode.value === 'long') {
          const requiredFields = [
            { field: 'custom_mother_name', label: 'Mother Name' },
            { field: 'custom_father_name', label: 'Father Name' },
            { field: 'custom_grade_interested_in', label: 'Grade Interested In' },
            { field: 'custom_child_date_of_birth', label: 'Child Date of Birth' },
            { field: 'custom_child_gender', label: 'Child Gender' },
            { field: 'custom_father_qualification', label: 'Father Educational Qualification' },
            { field: 'custom_mother_qualification', label: 'Mother Educational Qualification' },
            { field: 'custom_father_designation', label: 'Father Occupation' },
            { field: 'custom_father_organization', label: 'Father Organization' },
            { field: 'custom_mother_designation', label: 'Mother Occupation' },
            { field: 'custom_mother_organization', label: 'Mother Organization' },
            { field: 'custom_address_line_1', label: 'Address Line 1' },
            { field: 'custom_city', label: 'City' },
            { field: 'custom_zip_code', label: 'Zip Code' },
            { field: 'custom_father_mobile', label: 'Father Mobile Number' },
            { field: 'custom_mother_mobile', label: 'Mother Mobile Number' },
            { field: 'custom_father_email', label: 'Father Email Address' }
          ]
          
          for (const { field, label } of requiredFields) {
            if (!lead.doc[field]) {
              error.value = __(label + ' is mandatory')
              return error.value
            }
          }
          
          // Email validation for long form
          const emailFields = [
            { field: 'custom_father_email', label: 'Father Email' },
            { field: 'custom_mother_email', label: 'Mother Email' }
          ]
          
          for (const { field, label } of emailFields) {
            if (lead.doc[field] && !lead.doc[field].includes('@')) {
              error.value = __(label + ' is invalid')
              return error.value
            }
          }
          
          // Phone validation for long form
          const phoneFields = [
            { field: 'custom_father_mobile', label: 'Father Mobile Number' },
            { field: 'custom_mother_mobile', label: 'Mother Mobile Number' }
          ]
          
          for (const { field, label } of phoneFields) {
            if (lead.doc[field] && isNaN(lead.doc[field].replace(/[-+() ]/g, ''))) {
              error.value = __(label + ' should be a number')
              return error.value
            }
          }
        }
        
        // Short form validations
        if (lead.doc.annual_revenue) {
          if (typeof lead.doc.annual_revenue === 'string') {
            lead.doc.annual_revenue = lead.doc.annual_revenue.replace(/,/g, '')
          } else if (isNaN(lead.doc.annual_revenue)) {
            error.value = __('Annual Revenue should be a number')
            return error.value
          }
        }
        if (
          lead.doc.mobile_no &&
          isNaN(lead.doc.mobile_no.replace(/[-+() ]/g, ''))
        ) {
          error.value = __('Mobile No should be a number')
          return error.value
        }
        if (lead.doc.email && !lead.doc.email.includes('@')) {
          error.value = __('Invalid Email')
          return error.value
        }
        
        isLeadCreating.value = true
      },
      onSuccess(data) {
        capture('lead_created')
        isLeadCreating.value = false
        show.value = false
        router.push({ name: 'Lead', params: { leadId: data.name } })
        updateOnboardingStep('create_first_lead', true, false, () => {
          localStorage.setItem('firstLead' + user, data.name)
        })
      },
      onError(err) {
        isLeadCreating.value = false
        if (!err.messages) {
          error.value = err.message
          return
        }
        error.value = err.messages.join('\n')
      },
    },
  )
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'CRM Lead' }
  nextTick(() => (show.value = false))
}

onMounted(() => {
  lead.doc = { no_of_employees: '1-10' }
  Object.assign(lead.doc, props.defaults)

  if (!lead.doc?.lead_owner) {
    lead.doc.lead_owner = getUser().name
  }
  if (!lead.doc?.status && leadStatuses.value[0]?.value) {
    lead.doc.status = leadStatuses.value[0].value
  }
})
</script>
