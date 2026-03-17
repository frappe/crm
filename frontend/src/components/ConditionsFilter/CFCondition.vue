<template>
  <div
    class="flex gap-2"
    :class="[
      {
        'items-center': !props.isGroup,
      },
    ]"
  >
    <div
      class="flex gap-2 w-full"
      :class="[
        {
          'items-center justify-between': !props.isGroup,
        },
      ]"
    >
      <div :class="'text-end text-base text-ink-gray-5'">
        <div v-if="props.itemIndex == 0" class="min-w-[66px] text-start">
          {{ __('Where') }}
        </div>
        <div v-else class="min-w-[66px] flex items-start">
          <Button
            variant="subtle"
            class="w-max"
            icon-right="refresh-cw"
            :disabled="props.itemIndex > 2"
            :label="conjunction"
            @click="toggleConjunction"
          />
        </div>
      </div>
      <div v-if="!props.isGroup" class="flex items-center gap-2 w-full">
        <div id="fieldname" class="w-full">
          <Autocomplete
            :options="filterableFields.data"
            :modelValue="condition[0]"
            :placeholder="__('Field')"
            @update:modelValue="updateField"
          />
        </div>
        <div id="operator">
          <FormControl
            v-if="!condition[0]"
            disabled
            type="text"
            :placeholder="__('Operator')"
            class="w-[100px]"
          />
          <FormControl
            v-else
            v-model="condition[1]"
            :disabled="!condition[0]"
            type="select"
            :options="getOperators()"
            class="w-max min-w-[100px] text-ink-gray-8"
            @update:modelValue="updateOperator"
          />
        </div>
        <div id="value" class="w-full">
          <FormControl
            v-if="!condition[0]"
            disabled
            type="text"
            :placeholder="__('Condition')"
            class="w-full"
          />
          <component
            :is="getValueControl()"
            v-else
            v-model="condition[2]"
            :placeholder="__('Condition')"
            @change="updateValue"
          />
        </div>
      </div>
      <CFConditions
        v-if="props.isGroup && !(props.level == 2 || props.level == 4)"
        :conditions="condition"
        :isChild="true"
        :level="props.level"
        :disableAddCondition="props.disableAddCondition"
      />
      <Button
        v-if="props.isGroup && (props.level == 2 || props.level == 4)"
        variant="outline"
        :label="__('Open Nested Conditions')"
        @click="show = true"
      />
    </div>
    <div :class="'w-max'">
      <Dropdown placement="right" :options="dropdownOptions">
        <Button variant="ghost" icon="more-horizontal" />
      </Dropdown>
    </div>
  </div>
  <Dialog
    v-model="show"
    :options="{ size: '3xl', title: __('Nested Conditions') }"
  >
    <template #body-content>
      <CFConditions
        :conditions="condition"
        :isChild="true"
        :level="props.level"
        :disableAddCondition="props.disableAddCondition"
      />
    </template>
  </Dialog>
</template>

<script setup>
import GroupIcon from '~icons/lucide/group'
import UnGroupIcon from '~icons/lucide/ungroup'
import CFConditions from './CFConditions.vue'
import Link from '@/components/Controls/Link.vue'
import {
  Autocomplete,
  Button,
  DatePicker,
  DateRangePicker,
  DateTimePicker,
  Dialog,
  Dropdown,
  FormControl,
  Rating,
} from 'frappe-ui'
import { filterableFields } from './filterableFields'
import { reactive, computed, defineEmits, h, ref } from 'vue'

const show = ref(false)
const emit = defineEmits([
  'remove',
  'unGroupConditions',
  'toggleConjunction',
  'turnIntoGroup',
])

const props = defineProps({
  condition: { type: Array, required: true },
  isChild: { type: Boolean, default: false },
  itemIndex: { type: Number, default: 0 },
  level: { type: Number, default: 0 },
  isGroup: { type: Boolean, default: false },
  conjunction: { type: String, default: 'and' },
  disableAddCondition: { type: Boolean, default: false },
})

const condition = reactive(props.condition)

const dropdownOptions = computed(() => {
  const options = []

  if (!props.isGroup && props.level < 4) {
    options.push({
      label: __('Turn into a Group'),
      icon: () => h(GroupIcon),
      onClick: () => {
        emit('turnIntoGroup')
      },
    })
  }

  if (props.isGroup) {
    options.push({
      label: __('Ungroup Conditions'),
      icon: () => h(UnGroupIcon),
      onClick: () => {
        emit('unGroupConditions')
      },
    })
  }

  options.push({
    label: __('Remove'),
    icon: 'trash-2',
    variant: 'red',
    onClick: () => emit('remove'),
    condition: () => !props.isGroup,
  })

  options.push({
    label: __('Remove Group'),
    icon: 'trash-2',
    variant: 'red',
    onClick: () => emit('remove'),
    condition: () => props.isGroup,
  })

  return options
})

const typeCheck = ['Check']
const typeLink = ['Link', 'Dynamic Link']
const typeNumber = ['Float', 'Int', 'Currency', 'Percent']
const typeSelect = ['Select']
const typeString = ['Data', 'Long Text', 'Small Text', 'Text Editor', 'Text']
const typeDate = ['Date', 'Datetime']
const typeRating = ['Rating']

function toggleConjunction() {
  emit('toggleConjunction', props.conjunction)
}

const updateField = (field) => {
  condition[0] = field?.fieldname
  resetConditionValue()
}

const resetConditionValue = () => {
  condition[2] = ''
}

function getValueControl() {
  const [field, operator] = condition
  if (!field) return null
  const fieldData = filterableFields.data?.find((f) => f.fieldname == field)
  if (!fieldData) return null
  const { fieldtype, options } = fieldData
  if (operator == 'is') {
    return h(FormControl, {
      type: 'select',
      options: [
        {
          label: 'Set',
          value: 'set',
        },
        {
          label: 'Not Set',
          value: 'not set',
        },
      ],
    })
  } else if (['like', 'not like', 'in', 'not in'].includes(operator)) {
    return h(FormControl, { type: 'text' })
  } else if (typeSelect.includes(fieldtype) || typeCheck.includes(fieldtype)) {
    const _options =
      fieldtype == 'Check' ? ['Yes', 'No'] : getSelectOptions(options)
    return h(FormControl, {
      type: 'select',
      options: _options.map((o) => ({
        label: o,
        value: o,
      })),
    })
  } else if (typeLink.includes(fieldtype)) {
    if (fieldtype == 'Dynamic Link') {
      return h(FormControl, { type: 'text' })
    }
    return h(Link, {
      class: 'form-control',
      doctype: options,
      value: condition[2],
    })
  } else if (typeNumber.includes(fieldtype)) {
    return h(FormControl, { type: 'number' })
  } else if (typeDate.includes(fieldtype) && operator == 'between') {
    return h(DateRangePicker, { value: condition[2], iconLeft: '' })
  } else if (typeDate.includes(fieldtype)) {
    return h(fieldtype == 'Date' ? DatePicker : DateTimePicker, {
      value: condition[2],
      iconLeft: '',
    })
  } else if (typeRating.includes(fieldtype)) {
    return h(Rating, {
      modelValue: condition[2] || 0,
      class: 'truncate',
      'update:modelValue': (v) => updateValue(v),
    })
  } else {
    return h(FormControl, { type: 'text' })
  }
}

function updateValue(value) {
  value = value.target ? value.target.value : value
  if (condition[1] === 'between') {
    condition[2] = [value.split(',')[0], value.split(',')[1]]
  } else {
    condition[2] = isNaN(value) ? value : Number(value)
  }
}

function getSelectOptions(options) {
  return options.split('\n')
}

function updateOperator() {
  condition[2] = getDefaultValue(condition[0])
  resetConditionValue()
}

function getOperators() {
  let options = []
  const field = condition[0]
  if (!field) return options
  const fieldData = filterableFields.data?.find((f) => f.fieldname == field)
  if (!fieldData) return options
  const { fieldtype, fieldname } = fieldData
  if (typeString.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: '==' },
        { label: 'Not Equals', value: '!=' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
      ],
    )
  }
  if (fieldname === '_assign') {
    options = [
      { label: 'Like', value: 'like' },
      { label: 'Not Like', value: 'not like' },
      { label: 'Is', value: 'is' },
    ]
  }
  if (typeNumber.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: '==' },
        { label: 'Not Equals', value: '!=' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
        { label: '<', value: '<' },
        { label: '>', value: '>' },
        { label: '<=', value: '<=' },
        { label: '>=', value: '>=' },
      ],
    )
  }
  if (typeSelect.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: '==' },
        { label: 'Not Equals', value: '!=' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
      ],
    )
  }
  if (typeLink.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: '==' },
        { label: 'Not Equals', value: '!=' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
      ],
    )
  }
  if (typeCheck.includes(fieldtype)) {
    options.push(...[{ label: 'Equals', value: '==' }])
  }
  if (['Duration'].includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
      ],
    )
  }
  if (typeDate.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: '==' },
        { label: 'Not Equals', value: '!=' },
        { label: 'Is', value: 'is' },
        { label: '>', value: '>' },
        { label: '<', value: '<' },
        { label: '>=', value: '>=' },
        { label: '<=', value: '<=' },
        { label: 'Between', value: 'between' },
      ],
    )
  }
  if (typeRating.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: '==' },
        { label: 'Not Equals', value: '!=' },
        { label: 'Is', value: 'is' },
        { label: '>', value: '>' },
        { label: '<', value: '<' },
        { label: '>=', value: '>=' },
        { label: '<=', value: '<=' },
      ],
    )
  }
  const op = options.find((o) => o.value == condition[1])
  condition[1] = op?.value || options[0].value
  return options
}

function getDefaultValue(field) {
  if (typeSelect.includes(field.fieldtype)) {
    return getSelectOptions(field.options)[0]
  }
  if (typeCheck.includes(field.fieldtype)) {
    return 'Yes'
  }
  if (typeDate.includes(field.fieldtype)) {
    return null
  }
  if (typeRating.includes(field.fieldtype)) {
    return 0
  }
  return ''
}
</script>
