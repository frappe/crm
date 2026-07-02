<template>
  <div
    class="relative flex min-h-screen flex-col overflow-y-auto bg-surface-gray-1 transition-opacity duration-300 ease-out"
    :class="leaving ? 'opacity-0' : 'opacity-100'"
  >
    <div class="flex flex-1 flex-col justify-center px-4 py-10">
      <div class="mb-8 flex items-center justify-center gap-x-2">
        <CRMLogo class="size-7" />
        <span
          class="select-none text-3xl-semibold tracking-tight text-ink-gray-9"
        >
          {{ __('Frappe CRM') }}
        </span>
      </div>

      <Questionnaire
        :questions="questions"
        :show-skip="false"
        @submit="submitPersona"
      />

      <button
        type="button"
        class="mx-auto mt-6 block text-sm text-ink-gray-5 transition-colors hover:text-ink-gray-7"
        @click="skipPersonaForm"
      >
        {{ __('Skip for now') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import Questionnaire from '@/components/Questionnaire.vue'
import { call, usePageMeta } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { PERSONA_DONE_KEY } from '@/router'

const router = useRouter()
const { capture } = useTelemetry()
const leaving = ref(false)
const FADE_MS = 300

const leaveHome = async () => {
  leaving.value = true
  // Mark done client-side so a failed server persist can't re-loop the wizard.
  localStorage.setItem(PERSONA_DONE_KEY, '1')
  const fade = new Promise((resolve) => setTimeout(resolve, FADE_MS))
  const persist = call('frappe.client.set_value', {
    doctype: 'FCRM Settings',
    name: 'FCRM Settings',
    fieldname: 'persona_captured',
    value: 1,
  })
  try {
    await Promise.all([persist, fade])
  } catch (e) {
    await fade
  }
  router.push({ name: 'Home' })
}

const submitPersona = (answers) => {
  capture('onboarding_persona', answers)
  leaveHome()
}

const skipPersonaForm = () => {
  capture('onboarding_persona_skipped')
  leaveHome()
}

const questions = computed(() => [
  {
    key: 'current_solution',
    title: __('How are you managing your sales today?'),
    options: [
      { label: __('This is my first CRM'), value: 'first_crm' },
      { label: __('Spreadsheets'), value: 'spreadsheets' },
      { label: __('HubSpot'), value: 'hubspot' },
      { label: __('Salesforce'), value: 'salesforce' },
      { label: __('Zoho CRM'), value: 'zoho' },
      { label: __('Pipedrive'), value: 'pipedrive' },
      { label: __('Another CRM'), value: 'other_crm' },
      { label: __('Other'), value: 'other' },
    ],
  },
  {
    key: 'lead_sources',
    title: __('How do new leads usually come to you?'),
    multiple: true,
    options: [
      { label: __('Website forms'), value: 'website_forms' },
      { label: __('Facebook/Instagram Ads'), value: 'meta_ads' },
      { label: __('Google Ads'), value: 'google_ads' },
      { label: __('WhatsApp'), value: 'whatsapp' },
      { label: __('Email'), value: 'email' },
      { label: __('Phone calls'), value: 'phone_calls' },
      { label: __('Referrals'), value: 'referrals' },
      { label: __('Walk-ins'), value: 'walk_ins' },
      { label: __('CSV imports'), value: 'csv_imports' },
      { label: __('Other'), value: 'other' },
    ],
  },
  {
    key: 'biggest_challenges',
    title: __('What are your biggest challenges with sales today?'),
    multiple: true,
    options: [
      { label: __('Capturing leads'), value: 'capturing_leads' },
      { label: __('Following up consistently'), value: 'following_up' },
      { label: __('Keeping my pipeline organized'), value: 'pipeline_organized' },
      {
        label: __('Managing contacts and companies'),
        value: 'managing_contacts',
      },
      { label: __('Collaborating with my team'), value: 'team_collaboration' },
      { label: __('Reporting & forecasting'), value: 'reporting_forecasting' },
      { label: __('Replacing my current CRM'), value: 'replacing_crm' },
      { label: __('Other'), value: 'other' },
    ],
  },
  {
    key: 'team_size',
    title: __('How many people will use Frappe CRM?'),
    options: [
      { label: __('Just me'), value: 'just_me' },
      { label: __('2–5'), value: '2_5' },
      { label: __('6–20'), value: '6_20' },
      { label: __('More than 20'), value: 'more_than_20' },
    ],
  },
  {
    key: 'first_goal',
    title: __('What would you like to accomplish first?'),
    optional: true,
    options: [
      { label: __('Import my existing data'), value: 'import_data' },
      { label: __('Capture my first lead'), value: 'capture_lead' },
      { label: __('Set up my sales pipeline'), value: 'setup_pipeline' },
      { label: __('Organize my contacts'), value: 'organize_contacts' },
      { label: __('Invite my team'), value: 'invite_team' },
      { label: __('Close my first deal'), value: 'close_deal' },
      { label: __('Just exploring'), value: 'exploring' },
    ],
  },
])

usePageMeta(() => ({ title: __('Welcome to Frappe CRM') }))
</script>
