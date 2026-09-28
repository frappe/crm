<template>
  <div class="flex min-h-screen flex-col bg-surface-gray-1">
    <header class="flex items-center justify-between gap-4 px-6 py-4">
      <CRMLogo class="size-8 shrink-0" />
      <ol
        class="hidden items-center gap-2 sm:flex"
        :aria-label="__('Setup progress')"
      >
        <li
          v-for="(step, index) in steps"
          :key="step.name"
          class="flex items-center gap-2"
          :aria-current="index === current ? 'step' : undefined"
        >
          <span
            class="flex size-6 items-center justify-center rounded-full text-sm"
            :class="stepBadgeClass(step, index)"
          >
            <LucideCheck
              v-if="stepStatus[step.name] === 'completed'"
              class="size-3.5"
            />
            <template v-else>{{ index + 1 }}</template>
          </span>
          <span
            class="text-base"
            :class="
              index === current
                ? 'font-medium text-ink-gray-9'
                : 'text-ink-gray-5'
            "
          >
            {{ step.label }}
          </span>
          <LucideChevronRight
            v-if="index < steps.length - 1"
            class="size-4 text-ink-gray-4"
            aria-hidden="true"
          />
        </li>
      </ol>
      <Button
        v-if="!isLastStep"
        variant="ghost"
        :label="__('Skip setup')"
        @click="skipSetup"
      />
      <span v-else class="w-20" />
    </header>

    <main class="flex flex-1 justify-center px-4 pb-10 sm:items-center">
      <div
        class="grid w-full max-w-5xl overflow-hidden rounded-2xl bg-surface-white shadow-sm lg:grid-cols-2"
      >
        <section class="flex min-h-[600px] flex-col p-8 sm:p-10">
          <Button
            v-if="current > 0 && !isLastStep"
            variant="ghost"
            class="mb-4 self-start"
            icon-left="lucide-arrow-left"
            :label="__('Back')"
            @click="current--"
          />
          <component
            :is="activeStep.component"
            :key="activeStep.name"
            class="flex-1"
            @done="completeStep"
            @skip="skipStep"
            @finish="finishSetup"
          />
        </section>
        <SetupPreview class="hidden lg:flex" :step="activeStep.name" />
      </div>
    </main>
  </div>
</template>

<script setup>
import LucideCheck from '~icons/lucide/check'
import LucideChevronRight from '~icons/lucide/chevron-right'
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import SetupPreview from '@/components/Setup/SetupPreview.vue'
import SetupEmail from '@/components/Setup/SetupEmail.vue'
import SetupLeads from '@/components/Setup/SetupLeads.vue'
import SetupInvite from '@/components/Setup/SetupInvite.vue'
import SetupFeedback from '@/components/Setup/SetupFeedback.vue'
import { SETUP_DONE_KEY } from '@/router'
import { Button, call, usePageMeta } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { computed, markRaw, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { capture } = useTelemetry()

const steps = [
  { name: 'connect_email', label: __('Email'), component: markRaw(SetupEmail) },
  { name: 'bring_leads', label: __('Leads'), component: markRaw(SetupLeads) },
  { name: 'invite_team', label: __('Team'), component: markRaw(SetupInvite) },
  {
    name: 'feedback',
    label: __('Feedback'),
    component: markRaw(SetupFeedback),
  },
]

const current = ref(0)
const stepStatus = reactive({})

const activeStep = computed(() => steps[current.value])
const isLastStep = computed(() => current.value === steps.length - 1)

watch(activeStep, (step) => capture('setup_step_viewed', { step: step.name }), {
  immediate: true,
})

function stepBadgeClass(step, index) {
  if (index === current.value) return 'bg-surface-gray-9 text-ink-white'
  if (stepStatus[step.name] === 'completed') {
    return 'bg-surface-gray-7 text-ink-white'
  }
  return 'bg-surface-gray-3 text-ink-gray-6'
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
