<template>
  <SetupFlow
    v-model:step="stepName"
    :steps="steps"
    :labels="labels"
    @finish="finishSetup"
  >
    <template #brand>
      <div class="flex items-center gap-2">
        <CRMLogo class="size-6 shrink-0" aria-hidden="true" />
        <span class="text-base font-medium text-ink-gray-9">{{
          __('Frappe CRM')
        }}</span>
      </div>
    </template>
    <template #step="{ step, done, skip, handleBack }">
      <div class="flex flex-col">
        <Transition name="step" mode="out-in">
          <KeepAlive :include="['SetupLeads', 'SetupInvite']">
            <component
              :is="step.component"
              :ref="(view) => bindBack(view, handleBack)"
              :key="step.name"
              class="flex-1"
              @done="done"
              @skip="skip"
              @connect-email="stepName = 'connect_email'"
            />
          </KeepAlive>
        </Transition>
      </div>
    </template>
    <template #footer>
      <TelemetryConsent
        app-name="crm"
        class="mx-auto w-full max-w-md"
        :label="__('Help improve Frappe CRM by sharing anonymous usage data')"
        :error-message="__('Could not save your choice. Please try again.')"
      />
    </template>
    <template #preview="{ step }">
      <SetupPreview
        class="h-full"
        :step="step.name"
        :state="previewState"
        :handing-over="handingOver"
        @handed-over="openHome"
      />
    </template>
  </SetupFlow>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import SetupPreview from '@/components/Setup/SetupPreview.vue'
import SetupPassword from '@/components/Setup/SetupPassword.vue'
import SetupEmail from '@/components/Setup/SetupEmail.vue'
import SetupLeads from '@/components/Setup/SetupLeads.vue'
import SetupInvite from '@/components/Setup/SetupInvite.vue'
import { preloadLayout } from '@/components/Layouts/layouts'
import { call, usePageMeta } from 'frappe-ui'
import { SetupFlow, TelemetryConsent } from '@framework/ui/components/SetupFlow'
import { markRaw, provide, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const stepName = ref()

const steps = [
  window.needs_password_setup && {
    name: 'set_password',
    required: true,
    component: markRaw(SetupPassword),
  },
  { name: 'connect_email', component: markRaw(SetupEmail) },
  { name: 'bring_leads', component: markRaw(SetupLeads) },
  { name: 'invite_team', component: markRaw(SetupInvite) },
].filter(Boolean)

const labels = {
  back: __('Back'),
  skip: __('Skip setup'),
  skipTitle: __('Skip setup?'),
  skipMessage: __(
    "You won't see this guided setup again. You can still connect email, import leads and invite your team from Settings.",
  ),
  cancel: __('Cancel'),
  darkMode: __('Switch to dark mode'),
  lightMode: __('Switch to light mode'),
  stepOf: (step, total) => __('Step {0} of {1}', [step, total]),
}

const previewState = reactive({
  passwordLength: 0,
  passwordReady: false,
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

// The email and leads steps have screens of their own, which Back returns to first
let boundView = null
function bindBack(view, handleBack) {
  if (!view || view === boundView) return
  boundView = view
  handleBack(
    view.back
      ? { canGoBack: () => Boolean(view.canGoBack), back: () => view.back() }
      : null,
  )
}

// From lg up the preview goes Home and grows to fill the screen before Home opens, so setup
// ends without a cut. Below lg the preview is hidden, so Home opens at once.
const handingOver = ref(false)
let shellReady = Promise.resolve()

async function finishSetup() {
  await markSetupDone()
  if (!window.matchMedia?.('(min-width: 1024px)').matches) return openHome()
  // Home and the app shell load while the preview grows, so the switch shows no blank frame.
  shellReady = Promise.all([
    preloadLayout(window.innerWidth),
    import('@/pages/Home.vue'),
  ]).catch(() => {})
  handingOver.value = true
}

async function openHome() {
  await shellReady
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
