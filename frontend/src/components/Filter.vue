<template>
  <NestedPopover>
    <template #target>
      <Button label="Filter">
        <template #prefix><FilterIcon class="h-4" /></template>
        <template v-if="filterValues.length" #suffix>
          <div
            class="flex justify-center items-center w-5 h-5 text-2xs font-medium pt-[1px] bg-gray-900 text-white rounded"
          >
            {{ filterValues.length }}
          </div>
        </template>
      </Button>
    </template>
    <template #body="{ close }">
      <div class="rounded-lg border border-gray-100 bg-white shadow-xl my-2">
        <div class="p-2 min-w-[500px]">
          <div
            v-if="filterValues.length"
            v-for="(filter, i) in filterValues"
            id="filter-list"
            class="flex flex-col gap-2 mb-3"
          >
            <div class="flex items-center gap-2">
              <div class="text-gray-600 text-base pl-2 w-13 text-end">
                {{ i == 0 ? 'Where' : 'And' }}
              </div>
              <Autocomplete
                class="!min-w-[140px]"
                :value="filter.field"
                :options="filterableFields.data"
                @change="(e) => updateFilter(e, i)"
                placeholder="Filter by..."
              />
              <FormControl
                type="select"
                v-model="filter.operator"
                :options="getOperators(filter.fieldtype)"
                placeholder="Operator"
              />
              <FormControl
                class="!w-36"
                v-model="filter.value"
                type="text"
                placeholder="Value"
              />
              <Button variant="ghost" icon="x" @click="removeFilter(i)" />
            </div>
          </div>
          <div
            v-else
            class="text-gray-600 flex items-center text-sm px-3 h-7 mb-3"
          >
            Empty - Choose a field to filter by
          </div>
          <div class="flex items-center justify-between gap-2">
            <Autocomplete
              :options="filterableFields.data"
              value=""
              placeholder="filter by"
              @change="(e) => setfilter(e)"
            >
              <template #target="{ togglePopover }">
                <Button
                  class="!text-gray-600"
                  variant="ghost"
                  @click="togglePopover()"
                  label="Add filter"
                >
                  <template #prefix>
                    <FeatherIcon name="plus" class="h-4" />
                  </template>
                </Button>
              </template>
            </Autocomplete>
            <Button
              v-if="filterValues.length"
              class="!text-gray-600"
              variant="ghost"
              label="Clear all filter"
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
import {
  FeatherIcon,
  Button,
  Autocomplete,
  FormControl,
  createResource,
} from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const filterValues = ref([])

const filterableFields = createResource({
  url: 'crm.api.doc.get_filterable_fields',
  auto: true,
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

const typeCheck = ['Check']
const typeLink = ['Link']
const typeNumber = ['Float', 'Int']
const typeSelect = ['Select']
const typeString = ['Data', 'Long Text', 'Small Text', 'Text Editor', 'Text']

function getOperators(fieldtype) {
  let options = []
  if (typeString.includes(fieldtype) || typeNumber.includes(fieldtype)) {
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
  return options
}

function setfilter(data) {
  let operator = getOperators(data.fieldtype)[0].value
  filterValues.value = [
    ...filterValues.value,
    {
      field: data.value,
      operator: operator,
      value: '',
      label: data.label,
      fieldtype: data.fieldtype,
      options: data.options,
    },
  ]
}

function updateFilter(data, index) {
  let operator = getOperators(data.fieldtype)[0].value
  filterValues.value[index] = {
    field: data.value,
    operator: operator,
    value: '',
    label: data.label,
    fieldtype: data.fieldtype,
    options: data.options,
  }
}

function removeFilter(index) {
  filterValues.value.splice(index, 1)
}

function clearfilter(close) {
  filterValues.value = []
  close()
}
</script>
