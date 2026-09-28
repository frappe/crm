import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'

const pendingSteps = new Set()

export function useCrmOnboarding() {
  const onboarding = useOnboarding('frappecrm')
  const { capture } = useTelemetry()

  function completeStep(step, callback = null) {
    if (!onboarding) return
    // Checklist isn't set up yet (e.g. on /setup); the sidebar flushes these.
    if (!onboarding.totalSteps.value) {
      pendingSteps.add(step)
      return
    }
    const before = onboarding.stepsCompleted.value
    onboarding.updateOnboardingStep(step, true, false, callback)
    if (onboarding.stepsCompleted.value > before) {
      capture('onboarding_step_completed_' + step)
    }
  }

  function flushPendingSteps() {
    const steps = [...pendingSteps]
    pendingSteps.clear()
    steps.forEach((step) => completeStep(step))
  }

  return { completeStep, flushPendingSteps }
}
