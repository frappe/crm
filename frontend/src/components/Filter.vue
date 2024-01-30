<template>
  <NestedPopover>
    <template #target>
      <Button label="Filter">
        <template #prefix><FilterIcon class="h-4" /></template>
        <template v-if="filters?.size" #suffix>
          <div
            class="flex h-5 w-5 items-center justify-center rounded bg-gray-900 pt-[1px] text-2xs font-medium text-white"
          >
            {{ filters.size }}
          </div>
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="my-2 rounded-lg border border-gray-100 bg-white shadow-xl">
        <div class="min-w-[400px] p-2">
          <div
            v-if="filters?.size"
            v-for="(f, i) in filters"
            :key="i"
            id="filter-list"
            class="mb-3 flex items-center justify-between gap-2"
          >
            <div class="flex items-center gap-2">
              <div class="w-13 pl-2 text-end text-base text-gray-600">
                {{ i == 0 ? 'Where' : 'And' }}
              </div>
              <div id="fieldname" class="!min-w-[140px]">
                <Autocomplete
                  :value="f.field.fieldname"
                  :options="filterableFields.data"
                  @change="(e) => updateFilter(e, i)"
                  placeholder="Filter by..."
                />
              </div>
              <div id="operator">
                <FormControl
                  type="select"
                  :value="f.operator"
                  @change="(e) => updateOperator(e, f)"
                  :options="getOperators(f.field.fieldtype, f.field.fieldname)"
                  placeholder="Operator"
                />
              </div>
              <div id="value" class="!min-w-[140px]">
                <component
                  :is="getValSelect(f)"
                  :value="f.value"
                  @change="(v) => updateValue(v, f)"
                  placeholder="Value"
                />
              </div>
            </div>
            <Button variant="ghost" icon="x" @click="removeFilter(i)" />
          </div>
          <div
            v-else
            class="mb-3 flex h-7 items-center px-3 text-sm text-gray-600"
          >
            Empty - Choose a field to filter by
          </div>
          <div class="flex items-center justify-between gap-2">
            <Autocomplete
              value=""
              :options="filterableFields.data"
              @change="(e) => setfilter(e)"
              placeholder="Filter by..."
            >
              <template #target="{ togglePopover }">
                <Button
                  class="!text-gray-600"
                  variant="ghost"
                  @click="togglePopover()"
                  label="Add Filter"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              v-if="filters?.size"
              class="!text-gray-600"
              variant="ghost"
              label="Clear all Filter"
              @click="clearfilter(close)"
            />
          </div>
        </div>
      </div>
    </template>
  </NestedPopover>
</template>
<script setup>
import DatePicker from '@/components/Controls/DatePicker.vue'
import DateRangePicker from '@/components/Controls/DateRangePicker.vue'
import NestedPopover from '@/components/NestedPopover.vue'
import FilterIcon from '@/components/Icons/FilterIcon.vue'
import Link from '@/components/Controls/Link.vue'
import { FormControl, Autocomplete, createResource } from 'frappe-ui'
import { h, defineModel, computed } from 'vue'

const typeCheck = ['Check']
const typeLink = ['Link']
const typeNumber = ['Float', 'Int', 'Currency', 'Percent']
const typeSelect = ['Select']
const typeString = ['Data', 'Long Text', 'Small Text', 'Text Editor', 'Text']
const typeDate = ['Date', 'Datetime']

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
  default_filters: {
    type: Object,
    default: {},
  },
})

const emit = defineEmits(['update'])

const list = defineModel()

const filterableFields = createResource({
  url: 'crm.api.doc.get_filterable_fields',
  auto: true,
  cache: ['filterableFields', props.doctype],
  params: {
    doctype: props.doctype,
  },
  transform(fields) {
    fields = fields.map((field) => {
      return {
        label: field.label,
        value: field.fieldname,
        ...field,
      }
    })
    return fields
  },
})

const filters = computed(() => {
  if (!list.value?.data) return new Set()
  let allFilters = list.value?.params?.filters
  if (!allFilters || !filterableFields.data) return new Set()
  // remove default filters
  if (props.default_filters) {
    allFilters = removeCommonFilters(props.default_filters, allFilters)
  }
  return convertFilters(filterableFields.data, allFilters)
})

function removeCommonFilters(commonFilters, allFilters) {
  for (const key in commonFilters) {
    if (commonFilters.hasOwnProperty(key) && allFilters.hasOwnProperty(key)) {
      if (commonFilters[key] === allFilters[key]) {
        delete allFilters[key]
      }
    }
  }
  return allFilters
}

function convertFilters(data, allFilters) {
  let f = []
  for (let [key, value] of Object.entries(allFilters)) {
    let field = data.find((f) => f.fieldname === key)
    if (typeof value !== 'object') {
      value = ['=', value]
      if (field.fieldtype === 'Check') {
        value = ['equals', value[1] ? 'Yes' : 'No']
      }
    }
    // if (value[0] === 'LIKE' || value[0] === 'NOT LIKE') {
    //   value[1] = value[1].replace(/%/g, '')
    // }

    if (field) {
      f.push({
        field,
        fieldname: key,
        operator: oppositeOperatorMap[value[0]],
        value: value[1],
      })
    }
  }
  return new Set(f)
}

function getOperators(fieldtype, fieldname) {
  let options = []
  if (typeString.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not equals' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
      ]
    )
  }
  if (fieldname === '_assign') {
    // TODO: make equals and not equals work
    options = [
      { label: 'Like', value: 'like' },
      { label: 'Not Like', value: 'not like' },
      { label: 'Is', value: 'is' },
    ]
  }
  if (typeNumber.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not equals' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
        { label: '<', value: '<' },
        { label: '>', value: '>' },
        { label: '<=', value: '<=' },
        { label: '>=', value: '>=' },
      ]
    )
  }
  if (typeSelect.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not equals' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
      ]
    )
  }
  if (typeLink.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not equals' },
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
      ]
    )
  }
  if (typeCheck.includes(fieldtype)) {
    options.push(...[{ label: 'Equals', value: 'equals' }])
  }
  if (['Duration'].includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Like', value: 'like' },
        { label: 'Not Like', value: 'not like' },
        { label: 'In', value: 'in' },
        { label: 'Not In', value: 'not in' },
        { label: 'Is', value: 'is' },
      ]
    )
  }
  if (typeDate.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Is', value: 'is' },
        { label: '>', value: '>' },
        { label: '<', value: '<' },
        { label: '>=', value: '>=' },
        { label: '<=', value: '<=' },
        { label: 'Between', value: 'between' },
        { label: 'Timespan', value: 'timespan' },
      ]
    )
  }
  return options
}

function getValSelect(f) {
  const { field, operator } = f
  const { fieldtype, options } = field
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
  } else if (operator == 'timespan') {
    return h(FormControl, {
      type: 'select',
      options: timespanOptions,
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
    return h(Link, { class: 'form-control', doctype: options })
  } else if (typeNumber.includes(fieldtype)) {
    return h(FormControl, { type: 'number' })
  } else if (typeDate.includes(fieldtype) && operator == 'between') {
    return h(DateRangePicker)
  } else if (typeDate.includes(fieldtype)) {
    return h(DatePicker)
  } else {
    return h(FormControl, { type: 'text' })
  }
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
  return ''
}

function getDefaultOperator(fieldtype) {
  if (typeSelect.includes(fieldtype)) {
    return 'equals'
  }
  if (typeCheck.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    return 'equals'
  }
  if (typeDate.includes(fieldtype)) {
    return 'between'
  }
  return 'like'
}

function getSelectOptions(options) {
  return options.split('\n')
}

function setfilter(data) {
  if (!data) return
  filters.value.add({
    field: {
      label: data.label,
      fieldname: data.value,
      fieldtype: data.fieldtype,
      options: data.options,
    },
    fieldname: data.value,
    operator: getDefaultOperator(data.fieldtype),
    value: getDefaultValue(data),
  })
  apply()
}

function updateFilter(data, index) {
  filters.value.delete(Array.from(filters.value)[index])
  filters.value.add({
    fieldname: data.value,
    operator: getDefaultOperator(data.fieldtype),
    value: getDefaultValue(data),
    field: {
      label: data.label,
      fieldname: data.value,
      fieldtype: data.fieldtype,
      options: data.options,
    },
  })
  apply()
}

function removeFilter(index) {
  filters.value.delete(Array.from(filters.value)[index])
  apply()
}

function clearfilter(close) {
  filters.value.clear()
  apply()
  close()
}

function updateValue(value, filter) {
  value = value.target ? value.target.value : value
  if (filter.operator === 'between') {
    filter.value = [value.split(',')[0], value.split(',')[1]]
  } else {
    filter.value = value
  }
  apply()
}

function updateOperator(event, filter) {
  let oldOperatorValue = event.target._value
  let newOperatorValue = event.target.value
  filter.operator = event.target.value
  if (!isSameTypeOperator(oldOperatorValue, newOperatorValue)) {
    filter.value = getDefaultValue(filter.field)
  }
  if (newOperatorValue === 'is' || newOperatorValue === 'is not') {
    filter.value = 'set'
  }
  apply()
}

function isSameTypeOperator(oldOperator, newOperator) {
  let textOperators = [
    'like',
    'not like',
    'equals',
    'not equals',
    'in',
    'not in',
    '>',
    '<',
    '>=',
    '<=',
  ]
  if (
    textOperators.includes(oldOperator) &&
    textOperators.includes(newOperator)
  )
    return true
  return false
}

function apply() {
  let _filters = []
  filters.value.forEach((f) => {
    _filters.push({
      fieldname: f.fieldname,
      operator: f.operator,
      value: f.value,
    })
  })
  emit('update', parseFilters(_filters))
}

function parseFilters(filters) {
  const filtersArray = Array.from(filters)
  const obj = filtersArray.map(transformIn).reduce((p, c) => {
    if (['equals', '='].includes(c.operator)) {
      p[c.fieldname] =
        c.value == 'Yes' ? true : c.value == 'No' ? false : c.value
    } else {
      p[c.fieldname] = [operatorMap[c.operator.toLowerCase()], c.value]
    }
    return p
  }, {})
  const merged = { ...obj }
  return merged
}

function transformIn(f) {
  if (f.operator.includes('like') && !f.value.includes('%')) {
    f.value = `%${f.value}%`
  }
  return f
}

const operatorMap = {
  is: 'is',
  'is not': 'is not',
  in: 'in',
  'not in': 'not in',
  equals: '=',
  'not equals': '!=',
  yes: true,
  no: false,
  like: 'LIKE',
  'not like': 'NOT LIKE',
  '>': '>',
  '<': '<',
  '>=': '>=',
  '<=': '<=',
  between: 'between',
  timespan: 'timespan',
}

const oppositeOperatorMap = {
  is: 'is',
  '=': 'equals',
  '!=': 'not equals',
  equals: 'equals',
  'is not': 'is not',
  true: 'yes',
  false: 'no',
  LIKE: 'like',
  'NOT LIKE': 'not like',
  in: 'in',
  'not in': 'not in',
  '>': '>',
  '<': '<',
  '>=': '>=',
  '<=': '<=',
  between: 'between',
  timespan: 'timespan',
}

const timespanOptions = [
  {
    label: 'Last Week',
    value: 'last week',
  },
  {
    label: 'Last Month',
    value: 'last month',
  },
  {
    label: 'Last Quarter',
    value: 'last quarter',
  },
  {
    label: 'Last 6 Months',
    value: 'last 6 months',
  },
  {
    label: 'Last Year',
    value: 'last year',
  },
  {
    label: 'Yesterday',
    value: 'yesterday',
  },
  {
    label: 'Today',
    value: 'today',
  },
  {
    label: 'Tomorrow',
    value: 'tomorrow',
  },
  {
    label: 'This Week',
    value: 'this week',
  },
  {
    label: 'This Month',
    value: 'this month',
  },
  {
    label: 'This Quarter',
    value: 'this quarter',
  },
  {
    label: 'This Year',
    value: 'this year',
  },
  {
    label: 'Next Week',
    value: 'next week',
  },
  {
    label: 'Next Month',
    value: 'next month',
  },
  {
    label: 'Next Quarter',
    value: 'next quarter',
  },
  {
    label: 'Next 6 Months',
    value: 'next 6 months',
  },
  {
    label: 'Next Year',
    value: 'next year',
  },
]
</script>
