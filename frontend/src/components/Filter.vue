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
                <Link
                  v-if="typeLink.includes(f.field.fieldtype)"
                  class="form-control"
                  :value="f.value"
                  :doctype="f.field.options"
                  @change="(v) => updateValue(v, f)"
                  placeholder="Value"
                />
                <component
                  v-else
                  :is="getValSelect(f.field.fieldtype, f.field.options)"
                  :value="f.value"
                  @change="(e) => updateValue(e.target.value, f)"
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
import NestedPopover from '@/components/NestedPopover.vue'
import FilterIcon from '@/components/Icons/FilterIcon.vue'
import Link from '@/components/Controls/Link.vue'
import { FormControl, Autocomplete, createResource } from 'frappe-ui'
import { h, defineModel, computed } from 'vue'

const typeCheck = ['Check']
const typeLink = ['Link']
const typeNumber = ['Float', 'Int']
const typeSelect = ['Select']
const typeString = ['Data', 'Long Text', 'Small Text', 'Text Editor', 'Text']

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
      ]
    )
  }
  if (fieldname === '_assign') {
    options = [
      { label: 'Like', value: 'like' },
      { label: 'Not Like', value: 'not like' },
    ]
  }
  if (typeNumber.includes(fieldtype)) {
    options.push(
      ...[
        { label: '<', value: '<' },
        { label: '>', value: '>' },
        { label: '<=', value: '<=' },
        { label: '>=', value: '>=' },
        { label: 'Equals', value: 'equals' },
        { label: 'Not Equals', value: 'not equals' },
      ]
    )
  }
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    options.push(
      ...[
        { label: 'Is', value: 'is' },
        { label: 'Is Not', value: 'is not' },
      ]
    )
  }
  if (typeCheck.includes(fieldtype)) {
    options.push(...[{ label: 'Equals', value: 'equals' }])
  }
  return options
}

function getValSelect(fieldtype, options) {
  if (typeSelect.includes(fieldtype) || typeCheck.includes(fieldtype)) {
    const _options =
      fieldtype == 'Check' ? ['Yes', 'No'] : getSelectOptions(options)
    return h(FormControl, {
      type: 'select',
      options: _options.map((o) => ({
        label: o,
        value: o,
      })),
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
  return ''
}

function getDefaultOperator(fieldtype) {
  if (typeSelect.includes(fieldtype) || typeLink.includes(fieldtype)) {
    return 'is'
  }
  if (typeCheck.includes(fieldtype) || typeNumber.includes(fieldtype)) {
    return 'equals'
  }
  return 'like'
}

function getSelectOptions(options) {
  return options.split('\n')
}

function setfilter(data) {
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
  filter.value = value
  apply()
}

function updateOperator(event, filter) {
  filter.operator = event.target.value
  apply()
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
  const l__ = Array.from(filters)
  const obj = l__.map(transformIn).reduce((p, c) => {
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
  is: '=',
  'is not': '!=',
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
}

const oppositeOperatorMap = {
  '=': 'is',
  equals: 'equals',
  '!=': 'is not',
  true: 'yes',
  false: 'no',
  LIKE: 'like',
  'NOT LIKE': 'not like',
  '>': '>',
  '<': '<',
  '>=': '>=',
  '<=': '<=',
}
</script>
