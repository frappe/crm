export type StepValue = string | number

/** A step's state, derived from its position relative to the current step. */
export type StepState =
  | 'complete'
  | 'current'
  | 'upcoming'
  | 'failed'
  | 'skipped'

export type StepperSize = 'sm' | 'md'
export type StepperEdge = 'start' | 'end'

/** A step to render. Holds data only; the stepper never writes to it. */
export interface StepItem {
  /** Unique across the whole tree, sub-steps included. */
  value: StepValue

  /** Text shown for the step. */
  label: string

  /** Second line under the label. */
  description?: string

  /** Trailing text, such as a duration. */
  meta?: string

  /** The flow passed this step without doing it. */
  skipped?: boolean

  /** One level of sub-steps. Deeper nesting is ignored. */
  children?: StepItem[]
}

export interface StepperProps {
  /** Steps in order. */
  steps: StepItem[]

  /** Value of the current step; may be a sub-step's value. */
  modelValue?: StepValue | null

  /** Every step is done. Wins over `modelValue`. */
  completed?: boolean

  /** The current step is running: its indicator's outline spins. */
  loading?: boolean

  /** The current step failed. */
  failed?: boolean

  /** Lays the steps out as a vertical list instead of a segmented bar. */
  vertical?: boolean

  /** Vertical only: the side the indicators sit on. */
  edge?: StepperEdge

  /** Size of the indicators and text. */
  size?: StepperSize

  /** Vertical only: show sub-steps for every step, or only the current one. */
  substeps?: 'all' | 'current'

  /**
   * Finished steps become buttons that set `v-model`. Off while `completed`
   * is set, since `completed` would override the value a click sets.
   */
  clickable?: boolean
}

export interface StepperEmits {
  /** Fired when a finished step is clicked (`clickable` only). */
  'update:modelValue': [value: StepValue]
}

/** Props every `#step-*` slot receives. */
export interface StepSlotProps {
  item: StepItem
  /** Position among its siblings. */
  index: number
  state: StepState
}

/** A step with its derived state, as rendered. */
export interface ResolvedStep {
  item: StepItem
  index: number
  state: StepState
  children: ResolvedStep[]
}
