<template>
  <div class="flex min-h-screen flex-col bg-surface-gray-1">
    <header class="flex items-center justify-between gap-4 px-6 py-4">
      <CRMLogo class="size-8 shrink-0" />
      <Stepper
        v-model="activeStepName"
        class="hidden w-full max-w-xl sm:block"
        :steps="stepperSteps"
        :aria-label="__('Setup progress')"
        clickable
      />
      <Button
        v-if="!isLastStep"
        variant="ghost"
        :label="__('Skip setup')"
        @click="confirmSkipSetup"
      />
      <span v-else class="w-20" />
    </header>

    <main class="flex flex-1 justify-center px-4 pb-10 sm:items-center">
      <div
        class="grid w-full max-w-5xl overflow-hidden rounded-8 bg-surface-base shadow-sm lg:grid-cols-2"
      >
        <section class="flex min-h-[600px] flex-col p-8 sm:p-10">
          <div
            v-if="current > 0 && !isLastStep"
            class="mb-4 flex items-center justify-between"
          >
            <Button
              variant="ghost"
              icon-left="lucide-arrow-left"
              :label="__('Back')"
              @click="goBack"
            />
            <Button
              v-if="
                activeStep.name === 'about_you' && activeStepView?.canSkipQuestion
              "
              variant="ghost"
              class="!text-ink-gray-5"
              :label="__('Skip')"
              @click="activeStepView?.skipQuestion()"
            />
          </div>
          <KeepAlive include="SetupLeads,SetupPersona">
            <component
              ref="activeStepView"
              :is="activeStep.component"
              :key="activeStep.name"
              class="flex-1"
              @done="completeStep"
              @skip="skipStep"
              @finish="finishSetup"
            />
          </KeepAlive>
        </section>
        <SetupPreview
          class="hidden lg:flex"
          :step="activeStep.name"
          :state="previewState"
          :status="stepStatus"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import SetupPreview from '@/components/Setup/SetupPreview.vue'
import SetupEmail from '@/components/Setup/SetupEmail.vue'
import SetupLeads from '@/components/Setup/SetupLeads.vue'
import SetupInvite from '@/components/Setup/SetupInvite.vue'
import SetupPersona from '@/components/Setup/SetupPersona.vue'
import SetupFeedback from '@/components/Setup/SetupFeedback.vue'
import { SETUP_DONE_KEY } from '@/router'
import { globalStore } from '@/stores/global'
import Stepper from '@/components/Stepper/Stepper.vue'
import { Button, call, usePageMeta } from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, markRaw, provide, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { capture } = useTelemetry()
const { $dialog } = globalStore()

const steps = [
  { name: 'connect_email', label: __('Email'), component: markRaw(SetupEmail) },
  { name: 'bring_leads', label: __('Leads'), component: markRaw(SetupLeads) },
  { name: 'invite_team', label: __('Team'), component: markRaw(SetupInvite) },
  {
    name: 'about_you',
    label: __('About you'),
    component: markRaw(SetupPersona),
  },
  {
    name: 'feedback',
    label: __('Feedback'),
    component: markRaw(SetupFeedback),
  },
]

const current = ref(0)
const furthestStep = ref(0)
watch(
  current,
  (index) => {
    furthestStep.value = Math.max(furthestStep.value, index)
  },
  { flush: 'sync' },
)
const activeStepView = ref(null)
const stepStatus = reactive({})
const previewState = reactive({
  provider: null,
  importStage: null,
  importFile: '',
  importRows: 0,
  importProgress: null,
  importResult: null,
})
provide('setupPreview', previewState)

const activeStep = computed(() => steps[current.value])

const activeStepName = computed({
  get: () => activeStep.value.name,
  set: (name) => (current.value = steps.findIndex((s) => s.name === name)),
})

const stepperSteps = computed(() =>
  steps.map((step, index) => ({
    value: step.name,
    label: step.label,
    skipped: stepStatus[step.name] === 'skipped',
    selectable: index <= furthestStep.value,
  })),
)
const isLastStep = computed(() => current.value === steps.length - 1)

watch(activeStep, (step) => capture('setup_step_viewed', { step: step.name }), {
  immediate: true,
})

function goBack() {
  if (!activeStepView.value?.back?.()) current.value--
}

function completeStep(details = {}) {
  const step = activeStep.value.name
  stepStatus[step] = 'completed'
  capture('setup_step_completed', { step, ...details })
  current.value++
}

function skipStep() {
  const step = activeStep.value.name
  if (stepStatus[step] !== 'completed') stepStatus[step] = 'skipped'
  capture('setup_step_skipped', { step })
  current.value++
}

async function finishSetup({ rating, comment }) {
  capture('onboarding_feedback', {
    rating,
    comment,
    completed_steps: stepsWithStatus('completed'),
    skipped_steps: stepsWithStatus('skipped'),
  })
  await markSetupDone()
  router.replace({ name: 'Home' })
}

function stepsWithStatus(status) {
  return Object.keys(stepStatus).filter((name) => stepStatus[name] === status)
}

function confirmSkipSetup() {
  $dialog({
    title: __('Skip setup?'),
    message: __(
      "You won't see this guided setup again. You can still connect email, import leads and invite your team from Settings.",
    ),
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: __('Skip setup'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          skipSetup()
        },
      },
    ],
  })
}

async function skipSetup() {
  capture('setup_skipped', { step: activeStep.value.name })
  await markSetupDone()
  router.replace({ name: 'Home' })
}

async function markSetupDone() {
  try {
    await call('frappe.client.set_value', {
      doctype: 'FCRM Settings',
      name: 'FCRM Settings',
      fieldname: 'setup_completed',
      value: 1,
    })
    localStorage.setItem(SETUP_DONE_KEY, '1')
  } catch (error) {
    console.error('Failed to save setup status', error)
  }
}

usePageMeta(() => ({ title: __('Set up Frappe CRM') }))
</script>
