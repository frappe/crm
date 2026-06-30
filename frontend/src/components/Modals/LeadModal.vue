<template>
<Dialog v-model:open="show" :size="'3xl'">
  <template #body>
    <div class="bg-surface-elevation-2 px-4 pb-6 pt-5 sm:px-6">
      <!-- Header -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h3 class="text-3xl-semibold leading-6 text-ink-gray-9">
            {{
              showDuplicateDialog
                ? __('Potential Existing Leads')
                : __('Create Lead')
            }}
          </h3>
        </div>

        <div class="flex items-center gap-1">
          <Button
            v-if="
              !showDuplicateDialog &&
              isManager() &&
              !isMobileView
            "
            variant="ghost"
            class="w-7"
            :tooltip="__('Edit Fields Layout')"
            :icon="EditIcon"
            @click="openQuickEntryModal"
          />

          <Button
            variant="ghost"
            class="w-7"
            icon="lucide-x"
            @click="show = false"
          />
        </div>
      </div>

      <!-- Create Lead Form -->
      <template v-if="!showDuplicateDialog">
        <FieldLayout
          v-if="tabs.data"
          :tabs="tabs.data"
          :data="lead.doc"
        />

        <ErrorMessage
          v-if="error"
          class="mt-4"
          :message="__(error)"
        />
      </template>

      <!-- Duplicate Leads -->
      <template v-else>
        <div class="text-base text-ink-gray-6">
          {{
            __('We found {0} existing lead(s) with the same email address or mobile number.', [
              duplicateLeads.length,
            ])
          }}
        </div>

        <div class="mt-6 max-h-[420px] space-y-3 overflow-y-auto">

          <div
            v-for="duplicate in duplicateLeads"
            :key="duplicate.name"
            class="rounded-lg border border-outline-gray-2 p-4 transition-colors hover:border-outline-gray-4"
          >
            <div class="flex items-start justify-between gap-4">

              <div class="flex-1">

                <div class="text-lg font-semibold text-ink-gray-9">
                  {{ duplicate.lead_name }}
                </div>

                <div
                  v-if="duplicate.email"
                  class="mt-2 text-sm text-ink-gray-7"
                >
                  {{ duplicate.email }}
                </div>

                <div
                  v-if="duplicate.mobile_no"
                  class="text-sm text-ink-gray-7"
                >
                  {{ duplicate.mobile_no }}
                </div>

                <div
                  v-if="duplicate.organization"
                  class="mt-2 text-sm text-ink-gray-7"
                >
                  <strong>{{ __('Organization') }}:</strong>
                  {{ duplicate.organization }}
                </div>

                <div
                  v-if="duplicate.status"
                  class="text-sm text-ink-gray-7"
                >
                  <strong>{{ __('Status') }}:</strong>
                  {{ duplicate.status }}
                </div>

                <div class="mt-3">
                  <div class="mb-2 text-xs font-medium uppercase tracking-wide text-ink-gray-6">
                    {{ __('Matched By') }}
                  </div>

                  <div class="flex flex-wrap gap-2">
                    <span
                      v-for="match in duplicate.matched_on"
                      :key="match"
                      class="rounded-full bg-surface-gray-2 px-3 py-1 text-xs"
                    >
                      {{ match }}
                    </span>
                  </div>
                </div>

              </div>

              <Button
                variant="outline"
                :label="__('Open Lead')"
                @click.stop="openExistingLead(duplicate.name)"
              />

            </div>
          </div>

        </div>
      </template>
    </div>

    <!-- Footer -->
    <div class="px-4 pb-7 pt-4 sm:px-6">
      <div class="flex flex-row-reverse gap-2">

        <template v-if="!showDuplicateDialog">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isLeadCreating"
            @click="createNewLead"
          />
        </template>

        <template v-else>

          <Button
            variant="solid"
            :label="__('Create Anyway')"
            :loading="isLeadCreating"
            @click="continueAnyway"
          />

          <Button
            variant="subtle"
            :label="__('Back')"
            @click="goBack"
          />

        </template>

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
import { createResource } from 'frappe-ui'
import { useDocument } from '@/data/document'
import { computed, onMounted, ref, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: { type: Object, default: () => ({}) },
})

const { user } = sessionStore()
const { getUser, isManager } = usersStore()
const { getLeadStatus, statusOptions } = statusesStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const show = defineModel({ type: Boolean })
const router = useRouter()
const error = ref(null)
const isLeadCreating = ref(false)

const showDuplicateDialog = ref(false)
const duplicateLeads = ref([])

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
  url: 'frappe.client.insert',
})

const checkDuplicateLead = createResource({
  url: 'crm.fcrm.doctype.crm_lead.crm_lead.find_duplicate_leads',
})

function insertLead() {
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

        if (!lead.doc.first_name) {
          error.value = __('First Name is mandatory')
          return error.value
        }

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
          error.value = __('Mobile No. should be a number')
          return error.value
        }

        if (lead.doc.email && !lead.doc.email.includes('@')) {
          error.value = __('Invalid email address')
          return error.value
        }

        if (!lead.doc.status) {
          error.value = __('Status is required')
          return error.value
        }

        isLeadCreating.value = true
      },

      onSuccess(data) {
        capture('lead_created')
        isLeadCreating.value = false
        show.value = false
        lead.doc = {}

        router.push({
          name: 'Lead',
          params: {
            leadId: data.name,
          },
        })

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

async function createNewLead() {
  if (isLeadCreating.value) return

  isLeadCreating.value = true

  if (lead.doc.website && !lead.doc.website.startsWith('http')) {
    lead.doc.website = 'https://' + lead.doc.website
  }

  let existingLeads

  try {
    await triggerOnBeforeCreate?.()
    
    existingLeads = await checkDuplicateLead.submit({
      email: lead.doc.email,
      mobile_no: lead.doc.mobile_no,
    })
  } catch (err) {
    isLeadCreating.value = false
    error.value = err.message || __('Failed to check for duplicate leads')
    return
  }

  if (!existingLeads || existingLeads.length === 0) {
    insertLead()
    return
  }

  duplicateLeads.value = existingLeads
  showDuplicateDialog.value = true
  isLeadCreating.value = false
}

function continueAnyway() {
  showDuplicateDialog.value = false
  insertLead()
}

function goBack() {
  error.value = null
  showDuplicateDialog.value = false
}

function openExistingLead(leadName) {
  show.value = false

  router.push({
    name: 'Lead',
    params: {
      leadId: leadName,
    },
  })
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = {
    doctype: 'CRM Lead',
  }

  nextTick(() => (show.value = false))
}

watch(show, (value) => {
  if (!value) {
    showDuplicateDialog.value = false
    duplicateLeads.value = []
  }
})

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

