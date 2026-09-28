import { computed, reactive } from 'vue'

const capture = vi.fn()
let steps
let onboardingCompleted

vi.mock('frappe-ui/frappe', () => ({
  useTelemetry: () => ({ capture }),
  useOnboarding: () => ({
    stepsCompleted: computed(() => steps.filter((s) => s.completed).length),
    updateOnboardingStep: (name, value, skipped, callback) => {
      if (onboardingCompleted) return
      const step = steps.find((s) => s.name === name)
      if (step) step.completed = value
      callback?.(name, skipped)
    },
  }),
}))

const { useCrmOnboarding } = await import('@/composables/onboarding')

beforeEach(() => {
  capture.mockClear()
  onboardingCompleted = false
  steps = reactive([
    { name: 'create_first_lead', completed: false },
    { name: 'create_first_task', completed: true },
  ])
})

describe('useCrmOnboarding.completeStep', () => {
  it('captures a completion event the first time a step completes', () => {
    const { completeStep } = useCrmOnboarding()
    const callback = vi.fn()
    completeStep('create_first_lead', callback)
    expect(steps[0].completed).toBe(true)
    expect(callback).toHaveBeenCalledOnce()
    expect(capture).toHaveBeenCalledWith(
      'onboarding_step_completed_create_first_lead',
    )
  })

  it('does not capture again for an already completed step', () => {
    const { completeStep } = useCrmOnboarding()
    completeStep('create_first_task')
    expect(capture).not.toHaveBeenCalled()
  })

  it('does not capture for steps outside the checklist', () => {
    const { completeStep } = useCrmOnboarding()
    completeStep('create_first_note')
    expect(capture).not.toHaveBeenCalled()
  })

  it('does not capture once onboarding is finished', () => {
    onboardingCompleted = true
    const { completeStep } = useCrmOnboarding()
    completeStep('create_first_lead')
    expect(capture).not.toHaveBeenCalled()
  })
})
