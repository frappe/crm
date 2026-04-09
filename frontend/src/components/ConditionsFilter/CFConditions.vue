<template>
  <div
    class="rounded-lg border border-outline-gray-2 p-3 flex flex-col gap-4 w-full"
  >
    <template v-for="(condition, i) in conditions" :key="condition.field">
      <CFCondition
        v-if="Array.isArray(condition)"
        :condition="condition"
        :isChild="props.isChild"
        :itemIndex="i"
        :level="props.level + 1"
        :isGroup="isGroupCondition(condition[0])"
        :conjunction="getConjunction()"
        :disableAddCondition="props.disableAddCondition"
        :doctype="props.doctype"
        @remove="removeCondition(condition)"
        @unGroupConditions="unGroupConditions(condition)"
        @toggleConjunction="toggleConjunction"
        @turnIntoGroup="turnIntoGroup(condition)"
      />
    </template>
    <div v-if="props.isChild" class="flex">
      <Dropdown v-slot="{ open }" :options="dropdownOptions">
        <Button
          :disabled="props.disableAddCondition"
          :label="__('Add Condition')"
          icon-left="plus"
          :icon-right="open ? 'chevron-up' : 'chevron-down'"
        />
      </Dropdown>
    </div>
  </div>
</template>

<script setup>
import CFCondition from './CFCondition.vue'
import { filterableFields } from './filterableFields'
import { Button, Dropdown } from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  conditions: { type: Array, required: true },
  isChild: { type: Boolean, default: false },
  level: { type: Number, default: 0 },
  disableAddCondition: { type: Boolean, default: false },
  doctype: { type: String, required: true },
})

const conditions = reactive(props.conditions)

const getConjunction = () => {
  let conjunction = 'and'
  conditions.forEach((condition) => {
    if (typeof condition == 'string') {
      conjunction = condition
    }
  })
  return conjunction
}

const turnIntoGroup = (condition) => {
  conditions.splice(conditions.indexOf(condition), 1, [condition])
}

const isGroupCondition = (condition) => {
  return Array.isArray(condition)
}

const dropdownOptions = computed(() => {
  const options = [
    {
      label: __('Add Condition'),
      onClick: () => {
        const conjunction = getConjunction()
        conditions.push(conjunction, ['', '', ''])
      },
    },
  ]
  if (props.level < 3) {
    options.push({
      label: __('Add Condition Group'),
      onClick: () => {
        const conjunction = getConjunction()
        conditions.push(conjunction, [[]])
      },
    })
  }
  return options
})

function removeCondition(condition) {
  const conditionIndex = conditions.indexOf(condition)
  if (conditionIndex == 0) {
    conditions.splice(conditionIndex, 2)
  } else {
    conditions.splice(conditionIndex - 1, 2)
  }
}

function unGroupConditions(condition) {
  const conjunction = getConjunction()
  const newConditions = condition.map((c) => {
    if (typeof c == 'string') {
      return conjunction
    }
    return c
  })

  const index = conditions.indexOf(condition)
  if (index !== -1) {
    conditions.splice(index, 1, ...newConditions)
  }
}

function toggleConjunction(conjunction) {
  for (let i = 0; i < conditions.length; i++) {
    if (typeof conditions[i] == 'string') {
      conditions[i] = conjunction == 'and' ? 'or' : 'and'
    }
  }
}

watch(
  () => props.doctype,
  (doctype) => filterableFields.submit({ doctype }),
  { immediate: true },
)
</script>
