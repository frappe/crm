<template>
  <NestedPopover>
    <template #target>
      <Button label="Filter">
        <template #prefix><FilterIcon class="h-4" /></template>
        <template v-if="storage.size" #suffix>
          <div
            class="flex justify-center items-center w-5 h-5 text-2xs font-medium pt-[1px] bg-gray-900 text-white rounded"
          >
            {{ storage.size }}
          </div>
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="rounded-lg border border-gray-100 bg-white shadow-xl my-2">
        <div class="p-2 min-w-[400px]">
          <div
            v-if="storage.size"
            v-for="(f, i) in storage"
            :key="i"
            id="filter-list"
            class="flex items-center justify-between gap-2 mb-3"
          >
            <div class="flex items-center gap-2">
              <div class="text-gray-600 text-base pl-2 w-13 text-end">
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
                  v-model="f.operator"
                  :options="getOperators(f.field.fieldtype)"
                  placeholder="Operator"
                />
              </div>
              <div id="value" class="!min-w-[140px]">
                <SearchComplete
                  v-if="typeLink.includes(f.field.fieldtype)"
                  :doctype="f.field.options"
                  :value="f.value"
                  @change="(v) => (f.value = v.value)"
                  placeholder="Value"
                />
                <component
                  v-else
                  :is="getValSelect(f.field.fieldtype, f.field.options)"
                  v-model="f.value"
                  placeholder="Value"
                />
              </div>
            </div>
            <Button variant="ghost" icon="x" @click="removeFilter(i)" />
          </div>
          <div
            v-else
            class="text-gray-600 flex items-center text-sm px-3 h-7 mb-3"
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
              v-if="storage.size"
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
import SearchComplete from '@/components/SearchComplete.vue'
import { useDebounceFn } from '@vueuse/core'
import { useFilter } from '@/composables/filter'
import {
  FeatherIcon,
  Autocomplete,
  FormControl,
  createResource,
} from 'frappe-ui'
import { h, watch } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

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

const { apply, storage } = useFilter(() => filterableFields.data)
const typeCheck = ['Check']
const typeLink = ['Link']
const typeNumber = ['Float', 'Int']
const typeSelect = ['Select']
const typeString = ['Data', 'Long Text', 'Small Text', 'Text Editor', 'Text']

watch(
  storage,
  useDebounceFn(() => apply(), 300),
  { deep: true }
)

function getOperators(fieldtype) {
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
  storage.value.add({
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
}

function updateFilter(data, index) {
  storage.value.delete(Array.from(storage.value)[index])
  storage.value.add({
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
}

function removeFilter(index) {
  storage.value.delete(Array.from(storage.value)[index])
}

function clearfilter(close) {
  storage.value.clear()
  close()
}
</script>
