<template>
  <div class="flex flex-col">
    <fieldset :key="question.key" class="mx-0 min-w-0 border-0 p-0">
      <legend class="p-0 text-xl font-semibold text-ink-gray-9">
        {{ question.title }}
      </legend>
      <p class="mt-1 h-5 text-sm text-ink-gray-5">
        {{ question.multiple ? __('Select all that apply') : '' }}
      </p>
      <div class="mt-5 flex flex-wrap gap-2.5">
        <Button
          v-for="option in question.options"
          :key="option.value"
          :label="option.label"
          :variant="isSelected(option) ? 'solid' : 'outline'"
          size="md"
          class="!rounded-full"
          :aria-pressed="isSelected(option)"
          @click="select(option)"
        />
      </div>
    </fieldset>

    <div class="mt-auto flex items-center justify-between pt-8">
      <span class="text-sm font-medium text-ink-gray-5">
        {{ __('Step {0} of {1}', [current + 1, questions.length]) }}
      </span>
      <div class="flex items-center gap-2">
        <Button
          variant="subtle"
          icon-left="lucide-arrow-left"
          :label="__('Previous')"
          :disabled="current === 0"
          @click="current--"
        />
        <Button
          v-if="!isLast"
          variant="solid"
          icon-right="lucide-arrow-right"
          :label="__('Next')"
          :disabled="!canProceed"
          @click="current++"
        />
        <Button
          v-else
          variant="solid"
          :label="__('Finish')"
          :disabled="!canProceed"
          @click="finish"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, reactive, ref } from 'vue'

const emit = defineEmits(['done'])

const { capture } = useTelemetry()

const questions = [
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
      {
        label: __('Keeping my pipeline organized'),
        value: 'pipeline_organized',
      },
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
      { label: __('2-5'), value: '2_5' },
      { label: __('6-20'), value: '6_20' },
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
]

const current = ref(0)
const answers = reactive({})

const question = computed(() => questions[current.value])
const isLast = computed(() => current.value === questions.length - 1)

const canProceed = computed(() => {
  const value = answers[question.value.key]
  if (question.value.optional) return true
  return question.value.multiple ? Boolean(value?.length) : Boolean(value)
})

function isSelected(option) {
  const value = answers[question.value.key]
  if (question.value.multiple) return (value || []).includes(option.value)
  return value === option.value
}

function select(option) {
  const key = question.value.key
  if (!question.value.multiple) {
    answers[key] = option.value
    return
  }
  const value = answers[key] || []
  answers[key] = value.includes(option.value)
    ? value.filter((v) => v !== option.value)
    : [...value, option.value]
}

function finish() {
  capture('onboarding_persona', { ...answers })
  emit('done')
}
</script>
