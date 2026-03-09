<template>
  <CFConditions
    v-if="conditions.length > 0"
    :conditions="conditions"
    :level="0"
    :disableAddCondition="props.errors !== ''"
    :doctype="props.doctype"
  />
  <div
    v-if="conditions.length == 0"
    class="flex p-4 items-center cursor-pointer justify-center gap-2 text-sm border border-outline-gray-2 text-gray-600 rounded-md"
    @click="
      () => {
        conditions.push(['', '', ''])
        validateAssignmentRule(props.name)
      }
    "
  >
    <FeatherIcon name="plus" class="h-4" />
    {{ __('Add a Condition') }}
  </div>
  <div class="flex items-center justify-between mt-2">
    <div v-if="conditions.length > 0" class="">
      <Dropdown v-slot="{ open }" :options="dropdownOptions">
        <Button
          :disabled="props.errors !== ''"
          :icon-right="open ? 'chevron-up' : 'chevron-down'"
          :label="__('Add Condition')"
        />
      </Dropdown>
    </div>
    <ErrorMessage v-if="conditions.length > 0" :message="props.errors" />
  </div>
</template>

<script setup>
import { Button, Dropdown, ErrorMessage, FeatherIcon } from 'frappe-ui'
import { watchDebounced } from '@vueuse/core'
import { validateConditions } from '@/utils'
import CFConditions from '../../ConditionsFilter/CFConditions.vue'
import { inject, reactive } from 'vue'

const props = defineProps({
  conditions: { type: Array, default: () => [] },
  name: { type: String, default: '' },
  errors: { type: String, default: '' },
  doctype: { type: String, default: '' },
})

const conditions = reactive(props.conditions || [])
const validateAssignmentRule = inject('validateAssignmentRule')

const getConjunction = () => {
  let conjunction = 'and'
  conditions.forEach((condition) => {
    if (typeof condition == 'string') {
      conjunction = condition
    }
  })
  return conjunction
}

const dropdownOptions = [
  {
    label: __('Add Condition'),
    onClick: () => {
      addCondition()
    },
  },
  {
    label: __('Add Condition Group'),
    onClick: () => {
      const conjunction = getConjunction()
      conditions.push(conjunction, [[]])
    },
  },
]

const addCondition = () => {
  const isValid = validateConditions(conditions)

  if (!isValid) {
    return
  }
  const conjunction = getConjunction()

  conditions.push(conjunction, ['', '', ''])
}

watchDebounced(
  () => [...conditions],
  () => {
    validateAssignmentRule(props.name)
  },
  { deep: true, debounce: 300 },
)
</script>
