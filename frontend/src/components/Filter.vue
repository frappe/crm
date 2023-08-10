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
        <div class="p-2 min-w-[537px]">
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
                class="!w-32"
                v-model="filter.field"
                :options="[
                  { label: 'Name', value: 'lead_name' },
                  { label: 'Status', value: 'status' },
                ]"
                placeholder="Filter by..."
              />
              <FormControl
                type="select"
                v-model="filter.operator"
                :options="operators"
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
              :options="[
                { label: 'Name', value: 'lead_name' },
                { label: 'Status', value: 'status' },
              ]"
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

const filterValues = ref([])

const operators = ref([
  { label: 'Contains', value: 'contains' },
  { label: 'Equals', value: 'equals' },
  { label: 'Not Equals', value: 'not equals' },
  { label: 'Starts With', value: 'starts with' },
  { label: 'Ends With', value: 'ends with' },
  { label: 'Less Than', value: 'less than' },
  { label: 'Greater Than', value: 'greater than' },
  { label: 'Between', value: 'between' },
  { label: 'In', value: 'in' },
  { label: 'Not In', value: 'not in' },
  { label: 'Is', value: 'is' },
  { label: 'Is Not', value: 'is not' },
  { label: 'Is Set', value: 'is set' },
  { label: 'Is Not Set', value: 'is not set' },
])

function setfilter(data) {
  filterValues.value = [
    ...filterValues.value,
    {
      field: data.value,
      operator: 'contains',
      value: '',
    },
  ]
}

function removeFilter(index) {
  filterValues.value.splice(index, 1)
}

function clearfilter(close) {
  filterValues.value = []
  close()
}
</script>
