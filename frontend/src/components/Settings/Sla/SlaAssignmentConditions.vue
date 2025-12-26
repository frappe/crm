<template>
  <CFConditions
    v-if="props.conditions.length > 0"
    :conditions="props.conditions"
    :level="0"
    :disableAddCondition="slaDataErrors.condition != ''"
    :doctype="doctype"
  />
  <div
    v-if="props.conditions.length == 0"
    class="flex p-4 items-center cursor-pointer justify-center gap-2 text-sm border border-outline-gray-2 text-gray-600 rounded-md"
    @click="props.conditions.push(['', '', ''])"
  >
    <FeatherIcon name="plus" class="h-4" />
    {{ __('Add a custom condition') }}
  </div>
  <div class="flex items-center justify-between mt-2">
    <Dropdown
      v-if="props.conditions.length > 0"
      v-slot="{ open }"
      :options="dropdownOptions"
    >
      <Button
        :disabled="slaDataErrors.condition != ''"
        :icon-right="open ? 'chevron-up' : 'chevron-down'"
        :label="__('Add condition')"
      />
    </Dropdown>
    <ErrorMessage :message="slaDataErrors.condition" />
  </div>
</template>

<script setup>
import { Button, Dropdown, ErrorMessage, FeatherIcon } from 'frappe-ui'
import CFConditions from '../../ConditionsFilter/CFConditions.vue'
import { slaData, slaDataErrors, validateSlaData } from './utils'
import { watchDebounced } from '@vueuse/core'
import { validateConditions } from '../../../utils'
import { computed } from 'vue'

const props = defineProps({
  conditions: {
    type: Array,
    required: true,
  },
})

const doctype = computed(() => {
  return slaData.value.apply_on
})

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
    validateSlaData('condition')
  },
  { deep: true, debounce: 100 },
)
</script>
