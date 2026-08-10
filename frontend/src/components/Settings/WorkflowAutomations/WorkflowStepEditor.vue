<template>
  <div class="space-y-5">
    <div
      v-for="error in errors"
      :key="error.message"
      class="rounded border border-outline-red-2 bg-surface-red-1 p-2 text-sm text-ink-red-4"
      role="alert"
    >
      {{ error.message }}
    </div>

    <FormControl
      v-model="step.step_type"
      type="select"
      :label="__('Step Type')"
      :options="stepTypeOptions"
    />

    <template v-if="step.step_type === 'If'">
      <ConditionEditor
        v-model="step.step_condition"
        :doctype="targetDoctype"
        :label="__('Condition')"
        :placeholder="__('doc.status == \'Qualified\'')"
      />
      <div class="text-xs text-ink-gray-5">
        {{
          __(
            'Steps added under the If and Else arms run only when this decides that way.',
          )
        }}
      </div>
    </template>

    <template v-else-if="step.step_type === 'Wait'">
      <div class="flex items-start gap-2">
        <FormControl
          :model-value="params.value"
          type="number"
          class="w-24 shrink-0"
          :label="__('Wait')"
          @update:model-value="setParam('value', Number($event))"
        />
        <FormControl
          :model-value="params.unit || 'Minutes'"
          type="select"
          class="min-w-0 flex-1"
          :label="__('Unit')"
          :options="waitUnits"
          @update:model-value="setParam('unit', $event)"
        />
      </div>
    </template>

    <template v-else-if="step.step_type === 'WaitForEvent'">
      <FormControl
        :model-value="params.event_name"
        type="select"
        :label="__('Wait for')"
        :options="eventOptions"
        :placeholder="__('Choose an event')"
        @update:model-value="pickEvent($event)"
      />
      <FormControl
        v-if="correlationOptions.length"
        :model-value="params.correlation_key"
        type="select"
        :label="__('Belonging to')"
        :options="correlationOptions"
        @update:model-value="setParam('correlation_key', $event)"
      />
      <FormControl
        v-else
        :model-value="params.correlation_key"
        :label="__('Belonging to')"
        :placeholder="correlationPlaceholder"
        @update:model-value="setParam('correlation_key', $event)"
      />
      <div class="text-xs text-ink-gray-5">
        {{ __('Only the event raised for this record resumes the run.') }}
      </div>
      <div class="flex items-start gap-2">
        <FormControl
          :model-value="params.timeout_value"
          type="number"
          class="w-24 shrink-0"
          :label="__('Timeout')"
          @update:model-value="setParam('timeout_value', Number($event))"
        />
        <FormControl
          :model-value="params.timeout_unit || 'Days'"
          type="select"
          class="min-w-0 flex-1"
          :label="__('Unit')"
          :options="waitUnits"
          @update:model-value="setParam('timeout_unit', $event)"
        />
      </div>
    </template>

    <template v-else>
      <FormControl
        v-model="step.action_type"
        type="select"
        :label="__('Action')"
        :options="actionOptions"
        :placeholder="__('Choose what this step does')"
      />
      <TargetPicker
        v-if="targets.length > 1"
        v-model="step.target"
        :targets="targets"
        :label="__('Record')"
      />
      <ParamEditor
        :action="step"
        :schema="schema"
        :doctype="targetDoctype"
        :fields="fields"
      />
    </template>

    <ConditionEditor
      v-if="step.step_type !== 'If'"
      v-model="step.step_condition"
      :doctype="targetDoctype"
      :label="__('Only run when')"
      :placeholder="__('doc.status == \'Open\'')"
    />

    <div class="border-t border-outline-gray-2 pt-4">
      <button
        class="flex w-full items-center gap-1 text-sm text-ink-gray-5"
        :aria-expanded="showAdvanced"
        @click="showAdvanced = !showAdvanced"
      >
        <ChevronIcon class="size-4" :class="{ 'rotate-90': showAdvanced }" />
        {{ __('Advanced') }}
      </button>
      <div v-if="showAdvanced" class="mt-4 space-y-5">
        <FormControl
          v-model="step.step_key"
          :label="__('Step name')"
          :placeholder="suggestedKey"
          :description="
            __('Names this step in run logs and in its result path.')
          "
        />
        <FormControl
          v-if="schema?.output_schema"
          v-model="step.output_alias"
          :label="__('Name the result')"
          :placeholder="__('deal')"
          :description="__('Lets a later step act on what this one produced.')"
        />
        <div
          v-if="outputPaths.length"
          class="min-w-0 overflow-hidden rounded bg-surface-gray-2 p-3"
        >
          <div class="mb-1 text-xs-semibold text-ink-gray-5">
            {{ __('Available to later steps') }}
          </div>
          <div
            v-for="path in outputPaths"
            :key="path"
            class="break-all font-mono text-xs text-ink-gray-7"
          >
            {{ path }}
          </div>
        </div>
        <RelatedCondition v-model="step.related_condition" :targets="targets" />
      </div>
    </div>
  </div>
</template>

<script setup>
import ConditionEditor from './WorkflowConditionEditor.vue'
import ParamEditor from './WorkflowParamEditor.vue'
import RelatedCondition from './WorkflowRelatedCondition.vue'
import TargetPicker from './WorkflowTargetPicker.vue'
import {
  actionSchema,
  capabilitiesFor,
  stepParams,
} from './workflowCapabilities'
import { defaultStepKey } from './workflowSteps'
import ChevronIcon from '~icons/lucide/chevron-right'
import { FormControl } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  step: { type: Object, required: true },
  doc: { type: Object, required: true },
  targets: { type: Array, default: () => [] },
  errors: { type: Array, default: () => [] },
})

const stepTypeOptions = [
  { label: __('Action'), value: 'Action' },
  { label: __('Wait'), value: 'Wait' },
  { label: __('Wait for event'), value: 'WaitForEvent' },
  { label: __('If / Else'), value: 'If' },
]

const waitUnits = ['Seconds', 'Minutes', 'Hours', 'Days']
const correlationPlaceholder = '{{ doc.message_id or doc.name }}'

const showAdvanced = ref(false)

const params = computed(() => stepParams(props.step))
const suggestedKey = computed(() => defaultStepKey(props.step))

const targetDoctype = computed(
  () =>
    props.targets.find(
      (target) => target.alias === (props.step.target || 'trigger'),
    )?.doctype,
)

const fields = computed(
  () => capabilitiesFor(targetDoctype.value)?.fields || [],
)

const actionOptions = computed(() => {
  const actions = capabilitiesFor(targetDoctype.value)?.actions || []
  const options = actions.map((action) => ({
    label: action.label,
    value: action.action_type,
  }))
  // Never render a chosen action as an empty select, even if its DocType is still unknown.
  if (props.step.action_type && !actions.some(isChosen))
    options.unshift({
      label: schema.value?.label || props.step.action_type,
      value: props.step.action_type,
    })
  return options
})

function isChosen(action) {
  return action.action_type === props.step.action_type
}

const eventOptions = computed(
  () => capabilitiesFor(props.doc.document_type)?.custom_events || [],
)

const correlationOptions = computed(() => {
  const event = eventOptions.value.find(
    (option) => option.value === params.value.event_name,
  )
  return event?.correlation_options || []
})

/** Picking an event brings its default correlation with it, so the step works untouched. */
function pickEvent(name) {
  const event = eventOptions.value.find((option) => option.value === name)
  const suggested = event?.correlation_options?.[0]?.value
  props.step.params = JSON.stringify(
    { ...params.value, event_name: name, correlation_key: suggested || '' },
    null,
    2,
  )
}

const schema = computed(() =>
  actionSchema(targetDoctype.value, props.step.action_type),
)

const outputPaths = computed(() => {
  const keys = Object.keys(schema.value?.output_schema || {})
  const key = props.step.step_key || __('<step key>')
  return keys.map((name) => `context.steps.${key}.${name}`)
})

function setParam(name, value) {
  props.step.params = JSON.stringify(
    { ...params.value, [name]: value },
    null,
    2,
  )
}
</script>
