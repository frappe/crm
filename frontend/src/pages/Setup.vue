<template>
  <div class="grid min-h-screen bg-surface-base lg:grid-cols-2">
    <section class="flex min-h-screen flex-col px-6 py-5">
      <div class="flex h-8 items-center justify-between">
        <Button
          v-if="current > 0"
          variant="ghost"
          icon-left="lucide-arrow-left"
          :label="__('Back')"
          @click="goBack"
        />
        <span v-else />
        <Button
          variant="ghost"
          class="!text-ink-gray-5"
          :label="__('Skip setup')"
          @click="confirmSkipSetup"
        />
      </div>
      <main
        class="mx-auto flex w-full max-w-md flex-1 flex-col justify-center py-10"
      >
        <Progress
          :value="progress"
          :intervals="steps.length"
          size="sm"
          :aria-label="__('Step {0} of {1}', [current + 1, steps.length])"
        />
        <div class="mt-8 flex min-h-[520px] flex-col">
          <Transition name="step" mode="out-in">
            <KeepAlive include="SetupLeads">
              <component
                :is="activeStep.component"
                ref="activeStepView"
                :key="activeStep.name"
                class="flex-1"
                @done="completeStep"
                @skip="skipStep"
              />
            </KeepAlive>
          </Transition>
        </div>
      </main>
      <footer class="flex items-center gap-2 text-sm text-ink-gray-5">
        <CRMLogo class="size-4" />
        Frappe CRM
      </footer>
    </section>
    <SetupPreview
      class="sticky top-0 hidden h-screen lg:block"
      :step="activeStep.name"
      :state="previewState"
    />
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import SetupPreview from '@/components/Setup/SetupPreview.vue'
import SetupEmail from '@/components/Setup/SetupEmail.vue'
import SetupLeads from '@/components/Setup/SetupLeads.vue'
import SetupInvite from '@/components/Setup/SetupInvite.vue'
import { setupFeedback } from '@/composables/modals'
import { SETUP_DONE_KEY } from '@/router'
import { globalStore } from '@/stores/global'
import { Button, Progress, call, usePageMeta } from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, markRaw, provide, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { capture } = useTelemetry()
const { $dialog } = globalStore()

const steps = [
  { name: 'connect_email', component: markRaw(SetupEmail) },
  { name: 'bring_leads', component: markRaw(SetupLeads) },
  { name: 'invite_team', component: markRaw(SetupInvite) },
]

const current = ref(0)
const activeStepView = ref(null)
const stepStatus = reactive({})
const previewState = reactive({
  provider: null,
  email: '',
  importStage: null,
  importFile: '',
  importRows: 0,
  importProgress: null,
  importResult: null,
  invites: [],
})
provide('setupPreview', previewState)

const activeStep = computed(() => steps[current.value])
const progress = computed(() => ((current.value + 1) / steps.length) * 100)
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
  advance()
}

function skipStep() {
  const step = activeStep.value.name
  if (stepStatus[step] !== 'completed') stepStatus[step] = 'skipped'
  capture('setup_step_skipped', { step })
  advance()
}

function advance() {
  if (isLastStep.value) finishSetup(false)
  else current.value++
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
          capture('setup_skipped', { step: activeStep.value.name })
          finishSetup(true)
        },
      },
    ],
  })
}

async function finishSetup(skipped) {
  setupFeedback.value = {
    skipped_setup: skipped,
    completed_steps: stepsWithStatus('completed'),
    skipped_steps: stepsWithStatus('skipped'),
  }
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

<style scoped>
.step-enter-active,
.step-leave-active {
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}

.step-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.step-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (prefers-reduced-motion: reduce) {
  .step-enter-active,
  .step-leave-active {
    transition: none;
  }
}
</style>
