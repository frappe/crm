<template>
  <div class="grid min-h-screen bg-surface-base lg:grid-cols-2">
    <section class="flex min-h-screen flex-col px-6 py-5">
      <div class="flex h-8 items-center justify-between">
        <Button
          v-if="canGoBack || activeStepView?.canGoBack"
          variant="ghost"
          icon-left="lucide-arrow-left"
          :label="__('Back')"
          @click="goBack"
        />
        <span v-else />
        <div class="flex items-center gap-1">
          <Button
            v-if="activeStep.name !== 'set_password'"
            variant="ghost"
            class="!text-ink-gray-5"
            :label="__('Skip setup')"
            @click="confirmSkipSetup"
          />
          <Button
            variant="ghost"
            class="!text-ink-gray-5"
            :icon="isDark ? 'lucide-sun' : 'lucide-moon'"
            :tooltip="themeLabel"
            :aria-label="themeLabel"
            @click="toggleColorScheme"
          />
        </div>
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
      <SetupTelemetryConsent class="mb-3" />
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
import SetupPassword from '@/components/Setup/SetupPassword.vue'
import SetupEmail from '@/components/Setup/SetupEmail.vue'
import SetupLeads from '@/components/Setup/SetupLeads.vue'
import SetupInvite from '@/components/Setup/SetupInvite.vue'
import SetupTelemetryConsent from '@/components/Setup/SetupTelemetryConsent.vue'
import { setupFeedback } from '@/composables/modals'
import { globalStore } from '@/stores/global'
import { Button, Progress, call, useColorScheme, usePageMeta } from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { computed, markRaw, provide, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { capture } = useTelemetry()
const { $dialog } = globalStore()
const { resolvedColorScheme, toggleColorScheme } = useColorScheme()

const isDark = computed(() => resolvedColorScheme.value === 'dark')
const themeLabel = computed(() =>
  isDark.value ? __('Switch to light mode') : __('Switch to dark mode'),
)

const steps = [
  window.needs_password_setup && {
    name: 'set_password',
    component: markRaw(SetupPassword),
  },
  { name: 'connect_email', component: markRaw(SetupEmail) },
  { name: 'bring_leads', component: markRaw(SetupLeads) },
  { name: 'invite_team', component: markRaw(SetupInvite) },
].filter(Boolean)

const current = ref(0)
const activeStepView = ref(null)
const stepStatus = reactive({})
const previewState = reactive({
  passwordLength: 0,
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
const canGoBack = computed(
  () => current.value > 0 && steps[current.value - 1].name !== 'set_password',
)

const setupStartedAt = Date.now()
let stepStartedAt = setupStartedAt
const secondsSince = (start) => Math.round((Date.now() - start) / 1000)

capture('setup_started')
watch(
  activeStep,
  (step) => {
    stepStartedAt = Date.now()
    capture('setup_step_viewed', { step: step.name })
  },
  { immediate: true },
)

function goBack() {
  if (activeStepView.value?.back?.()) return
  capture('setup_back', { from_step: activeStep.value.name })
  current.value--
}

function completeStep(details = {}) {
  const step = activeStep.value.name
  stepStatus[step] = 'completed'
  capture('setup_step_completed', {
    step,
    time_on_step_s: secondsSince(stepStartedAt),
    ...details,
  })
  advance()
}

function skipStep() {
  const step = activeStep.value.name
  if (stepStatus[step] !== 'completed') stepStatus[step] = 'skipped'
  capture('setup_step_skipped', {
    step,
    time_on_step_s: secondsSince(stepStartedAt),
  })
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
  capture('setup_finished', {
    skipped,
    duration_s: secondsSince(setupStartedAt),
    steps_completed: setupFeedback.value.completed_steps.length,
  })
  await markSetupDone()
  router.replace({ name: 'Home' })
}

async function markSetupDone() {
  window.crm_setup_pending = false
  try {
    await call('frappe.client.set_value', {
      doctype: 'FCRM Settings',
      name: 'FCRM Settings',
      fieldname: 'setup_completed',
      value: 1,
    })
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
