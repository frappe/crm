<template>
  <Popover placement="bottom-end">
    <template #target="{ togglePopover, close }">
      <div class="flex items-center">
        <Button
          :label="__('Filter')"
          :class="filters?.length ? 'rounded-r-none' : ''"
          :iconLeft="FilterIcon"
          @click="togglePopover"
        >
          <template v-if="filters?.length" #suffix>
            <div
              class="flex h-5 w-5 items-center justify-center rounded-[5px] bg-surface-white pt-px text-xs font-medium text-ink-gray-8 shadow-sm"
            >
              {{ filters.length }}
            </div>
          </template>
        </Button>
        <Button
          v-if="filters?.length"
          :tooltip="__('Clear all filter')"
          class="rounded-l-none border-l"
          icon="x"
          @click.stop="clearfilter(close)"
        />
      </div>
    </template>
    <template #body="{ close }">
      <div
        class="my-2 min-w-40 rounded-lg bg-surface-modal shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
      >
        <div class="filters min-w-72 p-2 sm:min-w-[400px]">
          <div
            v-if="filters?.length"
            v-for="(f, i) in filters"
            :key="i"
            class="filter mb-4 sm:mb-3"
          >
            <div v-if="isMobileView" class="flex flex-col gap-2">
              <div class="-mb-2 flex w-full items-center justify-between">
                <div class="text-base text-ink-gray-5">
                  {{ i == 0 ? __('Where') : __('And') }}
                </div>
                <Button
                  class="flex"
                  variant="ghost"
                  icon="x"
                  @click="removeFilter(i)"
                />
              </div>
              <div id="fieldname" class="w-full">
                <Autocomplete
                  :value="f.field.fieldname"
                  :options="filterableFields"
                  @change="(e) => updateFilter(e, i)"
                  :placeholder="__('First name')"
                >
                  <template #item-label="{ option }">
                    <Tooltip :text="option.fieldname">
                      <div class="flex-1 truncate text-ink-gray-7">
                        {{ option.label }}
                      </div>
                    </Tooltip>
                  </template>
                </Autocomplete>
              </div>
              <div id="operator">
                <FormControl
                  type="select"
                  :value="f.operator"
                  @update:modelValue="(v) => updateOperator(v, f)"
                  :options="getOperators(f.field.fieldtype, f.field.fieldname)"
                  :placeholder="__('Equals')"
                />
              </div>
              <div id="value" class="w-full">
                <component
                  :is="getValueControl(f)"
                  v-model="f.value"
                  @change="(v) => updateValue(v, f)"
                  :placeholder="__('John Doe')"
                />
              </div>
            </div>
            <div v-else class="flex items-center justify-between gap-2">
              <div class="flex items-center gap-2">
                <div class="w-13 pl-2 text-end text-base text-ink-gray-5">
                  {{ i == 0 ? __('Where') : __('And') }}
                </div>
                <div id="fieldname" class="!min-w-[140px]">
                  <Autocomplete
                    :value="f.field.fieldname"
                    :options="filterableFields"
                    @change="(e) => updateFilter(e, i)"
                    :placeholder="__('First name')"
                  >
                    <template #item-label="{ option }">
                      <Tooltip :text="option.fieldname">
                        <div class="flex-1 truncate text-ink-gray-7">
                          {{ option.label }}
                        </div>
                      </Tooltip>
                    </template>
                  </Autocomplete>
                </div>
                <div id="operator">
                  <FormControl
                    type="select"
                    :defaultValue="f.operator"
                    @update:modelValue="(v) => updateOperator(v, f)"
                    :options="
                      getOperators(f.field.fieldtype, f.field.fieldname)
                    "
                    :placeholder="__('Equals')"
                  />
                </div>
                <div id="value" class="!min-w-[140px]">
                  <component
                    :is="getValueControl(f)"
                    v-model="f.value"
                    @change="(v) => updateValue(v, f)"
                    :placeholder="__('John Doe')"
                  />
                </div>
              </div>
              <Button
                class="flex"
                variant="ghost"
                icon="x"
                @click="removeFilter(i)"
              />
            </div>
          </div>
          <div
            v-else
            class="mb-3 flex h-7 items-center px-3 text-sm text-ink-gray-5"
          >
            {{ __('Empty - Choose a field to filter by') }}
          </div>
          <div class="flex items-center justify-between gap-2">
            <Autocomplete
              value=""
              :options="availableFilters"
              @change="(e) => setfilter(e)"
              :placeholder="__('First name')"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="!text-ink-gray-5"
                  variant="ghost"
                  :label="__('Add filter')"
                  iconLeft="plus"
                  @click="togglePopover()"
                />
              </template>
              <template #item-label="{ option }">
                <Tooltip :text="option.fieldname">
                  <div class="flex-1 truncate text-ink-gray-7">
                    {{ option.label }}
                  </div>
                </Tooltip>
              </template>
            </Autocomplete>
            <Button
              v-if="filters?.length"
              class="!text-ink-gray-5"
              variant="ghost"
              :label="__('Clear all filter')"
              @click="clearfilter(close)"
            />
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import FilterIcon from '@/components/Icons/FilterIcon.vue'
import Link from '@/components/Controls/Link.vue'
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { isMobileView } from '@/composables/settings'
import { getMeta } from '@/stores/meta'
import { useView } from '@/stores/view'
import {
  FormControl,
  Tooltip,
  Popover,
  DatePicker,
  DateTimePicker,
  DateRangePicker,
} from 'frappe-ui'
import { h, computed, inject, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const typeCheck = ['Check']
const typeLink = ['Link', 'Dynamic Link']
const typeNumber = ['Float', 'Int', 'Currency', 'Percent']
const typeSelect = ['Select']
const typeString = ['Data', 'Long Text', 'Small Text', 'Text Editor', 'Text']
const typeDate = ['Date', 'Datetime']

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

const props = defineProps({
  default_filters: {
    type: Object,
    default: {},
  },
})

const doctype = inject('doctype')
const viewName = inject('viewName')
const { currentView, resource } = useView(doctype, viewName)

const route = useRoute()
const router = useRouter()

const { getValueFields } = getMeta(doctype)

const emit = defineEmits(['update'])

const filterableFields = computed(() => {
  let _fields = getValueFields() || []

  if (props.default_filters) {
    _fields = _fields.filter((field) => {
      return !Object.keys(props.default_filters).includes(field.fieldname)
    })
  }

  return _fields.map((field) => ({
    ...field,
    label: field.label,
    value: field.fieldname,
  }))
})

const filters = computed(() => getInitialFilters())

function getInitialFilters(_filters) {
  let initialFilters = _filters || currentView.value?.filters || {}

  if (typeof initialFilters === 'object') {
    initialFilters = JSON.stringify(initialFilters)
  }
  initialFilters = JSON.parse(initialFilters) || {}

  if (props.default_filters) {
    initialFilters = removeCommonFilters(props.default_filters, initialFilters)
  }
  return convertFilters(initialFilters) || []
}

function getFiltersAsQuery(filters) {
  const query = {}
  for (const [key, value] of Object.entries(filters || {})) {
    query[key] = Array.isArray(value) ? JSON.stringify(value) : value
  }
  return query
}

function parseQueryToFilters(query) {
  const filters = {}
  for (const [key, value] of Object.entries(query || {})) {
    try {
      const parsed = JSON.parse(value)
      filters[key] = parsed
      continue
    } catch (e) {
      // value stays as-is when not JSON
    }
    filters[key] = value
  }
  return filters
}

function isSameObject(a, b) {
  return JSON.stringify(a || {}) === JSON.stringify(b || {})
}

function isEmptyQuery(query) {
  return !query || Object.keys(query).length === 0
}

watch(
  () => currentView.value?.filters,
  async (newFilters, oldFilters) => {
    if (newFilters == undefined && oldFilters == undefined) return
    if (!currentView.value) await resource.promise.value
    if (!currentView.value) return

    const queryFromFilters = getFiltersAsQuery(newFilters || {})
    const routeMatchesFilters = isSameObject(route.query, queryFromFilters)

    if (!routeMatchesFilters) {
      router.replace({ query: queryFromFilters })
    }
  },
  { deep: true, immediate: true },
)

watch(
  () => route.query,
  async (newQuery, oldQuery) => {
    if (!currentView.value) await resource.promise.value
    if (!currentView.value) return
    const filtersFromQuery = parseQueryToFilters(newQuery)
    const filtersMatchQuery = isSameObject(
      currentView.value.filters,
      filtersFromQuery,
    )

    if (!isEmptyQuery(newQuery) && !filtersMatchQuery) {
      currentView.value.filters = filtersFromQuery
      emit('update')
    }
  },
  { deep: true, immediate: true },
)

const availableFilters = computed(() => {
  if (!filterableFields.value) return []

  const selectedFieldNames = new Set(
    filters.value.map((filter) => filter.fieldname),
  )

  return filterableFields.value.filter(
    (field) => !selectedFieldNames.has(field.fieldname),
  )
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

function convertFilters(allFilters) {
  let f = []
  for (let [key, value] of Object.entries(allFilters)) {
    let field = filterableFields.value.find((f) => f.fieldname === key)
    if (typeof value !== 'object' || !value) {
      value = ['=', value]
      if (field?.fieldtype === 'Check') {
        value = ['equals', value[1] ? 'Yes' : 'No']
      }
    }

    if (field) {
      let operator = oppositeOperatorMap[value[0]]
      if (['like', 'not like'].includes(operator)) {
        value[1] = value[1].replace(/%/g, '')
      }

      f.push({
        field,
        fieldname: key,
        operator: operator,
        value: value[1],
      })
    }
  }
  return f
}

function getOperators(fieldtype, fieldname) {
  let options = []
  if (typeString.includes(fieldtype)) {
    options.push(
      ...[
        { label: __('Equals'), value: 'equals' },
        { label: __('Not equals'), value: 'not equals' },
        { label: __('Like'), value: 'like' },
        { label: __('Not like'), value: 'not like' },
        { label: __('In'), value: 'in' },
        { label: __('Not in'), value: 'not in' },
        { label: __('Is'), value: 'is' },
      ],
    )
  }
  if (fieldname === '_assign') {
    // TODO: make equals and not equals work
    options = [
      { label: __('Like'), value: 'like' },
      { label: __('Not like'), value: 'not like' },
      { label: __('Is'), value: 'is' },
    ]
  }
  if (typeNumber.includes(fieldtype)) {
    options.push(
      ...[
        { label: __('Equals'), value: 'equals' },
        { label: __('Not equals'), value: 'not equals' },
        { label: __('Like'), value: 'like' },
        { label: __('Not like'), value: 'not like' },
        { label: __('In'), value: 'in' },
        { label: __('Not in'), value: 'not in' },
        { label: __('Is'), value: 'is' },
        { label: __('<'), value: '<' },
        { label: __('>'), value: '>' },
        { label: __('<='), value: '<=' },
        { label: __('>='), value: '>=' },
      ],
    )
  }
  if (typeSelect.includes(fieldtype)) {
    options.push(
      ...[
        { label: __('Equals'), value: 'equals' },
        { label: __('Not equals'), value: 'not equals' },
        { label: __('In'), value: 'in' },
        { label: __('Not in'), value: 'not in' },
        { label: __('Is'), value: 'is' },
      ],
    )
  }
  if (typeLink.includes(fieldtype)) {
    options.push(
      ...[
        { label: __('Equals'), value: 'equals' },
        { label: __('Not equals'), value: 'not equals' },
        { label: __('Like'), value: 'like' },
        { label: __('Not like'), value: 'not like' },
        { label: __('In'), value: 'in' },
        { label: __('Not in'), value: 'not in' },
        { label: __('Is'), value: 'is' },
      ],
    )
  }
  if (typeCheck.includes(fieldtype)) {
    options.push(...[{ label: __('Equals'), value: 'equals' }])
  }
  if (['Duration'].includes(fieldtype)) {
    options.push(
      ...[
        { label: __('Like'), value: 'like' },
        { label: __('Not like'), value: 'not like' },
        { label: __('In'), value: 'in' },
        { label: __('Not in'), value: 'not in' },
        { label: __('Is'), value: 'is' },
      ],
    )
  }
  if (typeDate.includes(fieldtype)) {
    options.push(
      ...[
        { label: __('Equals'), value: 'equals' },
        { label: __('Not equals'), value: 'not equals' },
        { label: __('Is'), value: 'is' },
        { label: __('>'), value: '>' },
        { label: __('<'), value: '<' },
        { label: __('>='), value: '>=' },
        { label: __('<='), value: '<=' },
        { label: __('Between'), value: 'between' },
        { label: __('Timespan'), value: 'timespan' },
      ],
    )
  }
  return options
}

function getValueControl(f) {
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
      value: f.value,
      type: 'select',
      options: _options.map((o) => ({
        label: o,
        value: o,
      })),
      'onUpdate:modelValue': (v) => updateValue(v, f),
    })
  } else if (typeLink.includes(fieldtype)) {
    if (fieldtype == 'Dynamic Link') {
      return h(FormControl, { type: 'text' })
    }
    return h(Link, { class: 'form-control', doctype: options, value: f.value })
  } else if (typeNumber.includes(fieldtype)) {
    return h(FormControl, { type: 'number' })
  } else if (typeDate.includes(fieldtype) && operator == 'between') {
    return h(DateRangePicker, { value: f.value, iconLeft: '' })
  } else if (typeDate.includes(fieldtype)) {
    return h(fieldtype == 'Date' ? DatePicker : DateTimePicker, {
      value: f.value,
      iconLeft: '',
    })
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
  filters.value.push({
    field: {
      label: data.label,
      fieldname: data.fieldname,
      fieldtype: data.fieldtype,
      options: data.options,
    },
    fieldname: data.fieldname,
    operator: getDefaultOperator(data.fieldtype),
    value: getDefaultValue(data),
  })
  apply()
}

function updateFilter(data, index) {
  if (!data.fieldname) return

  filters.value.splice(index, 1, {
    fieldname: data.fieldname,
    operator: getDefaultOperator(data.fieldtype),
    value: getDefaultValue(data),
    field: {
      label: data.label,
      fieldname: data.fieldname,
      fieldtype: data.fieldtype,
      options: data.options,
    },
  })
  apply()
}

function removeFilter(index) {
  filters.value.splice(index, 1)
  apply()
}

function clearfilter(close) {
  filters.value.length = 0
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

function updateOperator(value, filter) {
  let oldOperatorValue = filter.operator
  let newOperatorValue = value
  filter.operator = value
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
  currentView.value.filters = parseFilters(_filters) || {}
  emit('update')
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

const timespanOptions = [
  {
    label: __('Last week'),
    value: 'last week',
  },
  {
    label: __('Last month'),
    value: 'last month',
  },
  {
    label: __('Last quarter'),
    value: 'last quarter',
  },
  {
    label: __('Last 6 months'),
    value: 'last 6 months',
  },
  {
    label: __('Last year'),
    value: 'last year',
  },
  {
    label: __('Yesterday'),
    value: 'yesterday',
  },
  {
    label: __('Today'),
    value: 'today',
  },
  {
    label: __('Tomorrow'),
    value: 'tomorrow',
  },
  {
    label: __('This week'),
    value: 'this week',
  },
  {
    label: __('This month'),
    value: 'this month',
  },
  {
    label: __('This quarter'),
    value: 'this quarter',
  },
  {
    label: __('This year'),
    value: 'this year',
  },
  {
    label: __('Next week'),
    value: 'next week',
  },
  {
    label: __('Next month'),
    value: 'next month',
  },
  {
    label: __('Next quarter'),
    value: 'next quarter',
  },
  {
    label: __('Next 6 months'),
    value: 'next 6 months',
  },
  {
    label: __('Next year'),
    value: 'next year',
  },
]
</script>
