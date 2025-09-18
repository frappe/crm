<template>
  <CFConditions
    v-if="props.conditions.length > 0"
    :conditions="props.conditions"
    :level="0"
    :disableAddCondition="props.errors !== ''"
    :doctype="props.doctype"
  />
  <div
    v-if="props.conditions.length == 0"
    class="flex p-4 items-center cursor-pointer justify-center gap-2 text-sm border border-outline-gray-2 text-gray-600 rounded-md"
    @click="
      () => {
        props.conditions.push(['', '', ''])
        validateAssignmentRule(props.name)
      }
    "
  >
    <FeatherIcon name="plus" class="h-4" />
    {{ __('Add a condition') }}
  </div>
  <div class="flex items-center justify-between mt-2">
    <div class="" v-if="props.conditions.length > 0">
      <Dropdown v-slot="{ open }" :options="dropdownOptions">
        <Button
          :disabled="props.errors !== ''"
          :icon-right="open ? 'chevron-up' : 'chevron-down'"
          :label="__('Add condition')"
        />
      </Dropdown>
    </div>
    <ErrorMessage v-if="props.conditions.length > 0" :message="props.errors" />
  </div>
</template>

<script setup>
import { Button, Dropdown, ErrorMessage, FeatherIcon } from 'frappe-ui'
import { watchDebounced } from '@vueuse/core'
import { validateConditions } from '@/utils'
import CFConditions from '../../ConditionsFilter/CFConditions.vue'
import { inject } from 'vue'

const props = defineProps({
  conditions: Array,
  name: String,
  errors: String,
  doctype: String,
})

const validateAssignmentRule = inject('validateAssignmentRule')

const getConjunction = () => {
  let conjunction = 'and'
  props.conditions.forEach((condition) => {
    if (typeof condition == 'string') {
      conjunction = condition
    }
  })
  return conjunction
}

const dropdownOptions = [
  {
    label: __('Add condition'),
    onClick: () => {
      addCondition()
    },
  },
  {
    label: __('Add condition group'),
    onClick: () => {
      const conjunction = getConjunction()
      props.conditions.push(conjunction, [[]])
    },
  },
]

const addCondition = () => {
  const isValid = validateConditions(props.conditions)

  if (!isValid) {
    return
  }
  const conjunction = getConjunction()

  props.conditions.push(conjunction, ['', '', ''])
}

watchDebounced(
  () => [...props.conditions],
  () => {
    validateAssignmentRule(props.name)
  },
  { deep: true, debounce: 300 },
)
</script>
