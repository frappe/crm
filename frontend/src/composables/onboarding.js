import { useOnboarding, useTelemetry } from 'frappe-ui/frappe'

export function useCrmOnboarding() {
  const onboarding = useOnboarding('frappecrm')
  const { capture } = useTelemetry()

  function completeStep(step, callback = null) {
    if (!onboarding) return
    const before = onboarding.stepsCompleted.value
    onboarding.updateOnboardingStep(step, true, false, callback)
    if (onboarding.stepsCompleted.value > before) {
      capture('onboarding_step_completed_' + step)
    }
  }

  return { completeStep }
}
