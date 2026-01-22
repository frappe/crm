<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-header>
      <div class="mb-6 flex items-center justify-between">
        <div>
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Convert to deal') }}
          </h3>
        </div>
        <div class="flex items-center gap-1">
          <Button
            v-if="isManager() && !isMobileView"
            variant="ghost"
            :tooltip="__('Edit deal\'s mandatory fields layout')"
            :icon="EditIcon"
            @click="openQuickEntryModal"
          />
          <Button icon="x" variant="ghost" @click="show = false" />
        </div>
      </div>
    </template>
    <template #body-content>
      <div class="mb-4 flex items-center gap-2 text-ink-gray-5">
        <OrganizationsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Organization') }}</label>
      </div>
      <div class="ml-6 text-ink-gray-9">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose existing') }}</div>
          <Switch v-model="existingOrganizationChecked" />
        </div>
        <Link
          v-if="existingOrganizationChecked"
          class="form-control mt-2.5"
          size="md"
          :value="existingOrganization"
          doctype="CRM Organization"
          @change="(data) => (existingOrganization = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{
            __(
              'New organization will be created based on the data in details section',
            )
          }}
        </div>
      </div>

      <div class="mb-4 mt-6 flex items-center gap-2 text-ink-gray-5">
        <ContactsIcon class="h-4 w-4" />
        <label class="block text-base">{{ __('Contact') }}</label>
      </div>
      <div class="ml-6 text-ink-gray-9">
        <div class="flex items-center justify-between text-base">
          <div>{{ __('Choose existing') }}</div>
          <Switch v-model="existingContactChecked" />
        </div>
        <Link
          v-if="existingContactChecked"
          class="form-control mt-2.5"
          size="md"
          :value="existingContact"
          doctype="Contact"
          @change="(data) => (existingContact = data)"
        />
        <div v-else class="mt-2.5 text-base">
          {{ __("New contact will be created based on the person's details") }}
        </div>
      </div>

      <div v-if="dealTabs.data?.length" class="h-px w-full border-t my-6" />

      <FieldLayout
        v-if="dealTabs.data?.length"
        :tabs="dealTabs.data"
        :data="deal.doc"
        doctype="CRM Deal"
      />
      <ErrorMessage class="mt-4" :message="error" />
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button :label="__('Convert')" variant="solid" @click="convertToDeal" />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import Link from '@/components/Controls/Link.vue'
import { useDocument } from '@/data/document'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { statusesStore } from '@/stores/statuses'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { isMobileView } from '@/composables/settings'
import { capture } from '@/telemetry'
import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'
import { Switch, Dialog, createResource, call } from 'frappe-ui'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  lead: {
    type: Object,
    required: true,
  },
})

const show = defineModel()

const router = useRouter()

const { statusOptions, getDealStatus } = statusesStore()
const { isManager } = usersStore()
const { user } = sessionStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')

const existingContactChecked = ref(false)
const existingOrganizationChecked = ref(false)

const existingContact = ref('')
const existingOrganization = ref('')
const error = ref('')
const $telemetry = useTelemetry()

const { triggerConvertToDeal } = useDocument('CRM Lead', props.lead.name)
const { document: deal } = useDocument('CRM Deal')

async function convertToDeal() {
  error.value = ''

  if (existingContactChecked.value && !existingContact.value) {
    error.value = __('Please select an existing contact')
    return
  }

  if (existingOrganizationChecked.value && !existingOrganization.value) {
    error.value = __('Please select an existing organization')
    return
  }

  if (!existingContactChecked.value && existingContact.value) {
    existingContact.value = ''
  }

  if (!existingOrganizationChecked.value && existingOrganization.value) {
    existingOrganization.value = ''
  }

  await triggerConvertToDeal?.(props.lead, deal.doc, () => (show.value = false))

  let _deal = await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', {
    lead: props.lead.name,
    deal: deal.doc,
    existing_contact: existingContact.value,
    existing_organization: existingOrganization.value,
  }).catch((err) => {
    if (err.exc_type == 'MandatoryError') {
      const errorMessage = err.messages
        .map((msg) => {
          let arr = msg.split(': ')
          return arr[arr.length - 1].trim()
        })
        .join(', ')

      if (errorMessage.toLowerCase().includes('required')) {
        error.value = __(errorMessage)
      } else {
        error.value = __('{0} is required', [errorMessage])
      }
      return
    }
    error.value = __('Error converting to deal: {0}', [err.messages?.[0]])
  })
  if (_deal) {
    show.value = false
    existingContactChecked.value = false
    existingOrganizationChecked.value = false
    existingContact.value = ''
    existingOrganization.value = ''
    error.value = ''
    updateOnboardingStep('convert_lead_to_deal', true, false, () => {
      localStorage.setItem('firstDeal' + user, _deal)
    })
    capture('convert_lead_to_deal')
    $telemetry.capture('convert_lead_to_deal', true)
    router.push({ name: 'Deal', params: { dealId: _deal } })
  }
}

const dealStatuses = computed(() => {
  let statuses = statusOptions('deal')
  if (!deal.doc?.status) {
    deal.doc.status = statuses[0].value
  }
  return statuses
})

const dealTabs = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_fields_layout',
  cache: ['RequiredFields', 'CRM Deal'],
  params: { doctype: 'CRM Deal', type: 'Required Fields' },
  auto: true,
  transform: (_tabs) => {
    let hasFields = false
    let parsedTabs = _tabs?.forEach((tab) => {
      tab.sections?.forEach((section) => {
        section.columns?.forEach((column) => {
          column.fields?.forEach((field) => {
            hasFields = true
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = dealStatuses.value
              field.prefix = getDealStatus(deal.doc.status).color
            }

            if (field.fieldtype === 'Table') {
              deal.doc[field.fieldname] = []
            }
          })
        })
      })
    })
    return hasFields ? parsedTabs : []
  },
})

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = {
    doctype: 'CRM Deal',
    onlyRequired: true,
  }
  show.value = false
}
</script>
