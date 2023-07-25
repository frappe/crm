<template>
  <div id="header" class="flex justify-between items-center px-5 py-4">
    <div class="left flex space-x-2">
      <h1 class="font-semibold text-xl">{{ title }}</h1>
    </div>
    <div class="right flex space-x-2">
      <Button variant="solid" label="Create">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </div>
  </div>
  <div
    id="sub-header"
    class="flex justify-between items-center px-5 pb-3 border-b"
  >
    <div class="left flex space-x-2">
      <Dropdown :options="viewsDropdownOptions">
        <template #default="{ open }">
          <Button
            :label="currentView.label"
            :icon-right="open ? 'chevron-up' : 'chevron-down'"
          >
            <template #prefix
              ><FeatherIcon :name="currentView.icon" class="h-4"
            /></template>
          </Button>
        </template>
      </Dropdown>
    </div>
    <div class="right flex space-x-2">
      <Button label="Sort">
        <template #prefix><SortIcon class="h-4" /></template>
      </Button>
      <Button label="Filter">
        <template #prefix><FilterIcon class="h-4" /></template>
      </Button>
      <Button icon="more-horizontal" />
    </div>
  </div>
  <div id="content" class="flex flex-col w-full overflow-x-auto flex-1">
    <div class="flex flex-col overflow-y-hidden w-max min-w-full">
      <div
        id="list-header"
        class="flex space-x-4 items-center px-5 py-2 border-b"
      >
        <Checkbox class="" />
        <div
          v-for="column in columns"
          :key="column"
          class="text-sm text-gray-600"
          :class="[column.size, column.align]"
        >
          {{ column.label }}
        </div>
      </div>
      <div id="list-rows" class="h-full overflow-y-auto">
        <div
          v-for="row in rows"
          :key="row"
          class="flex space-x-4 items-center mx-2 px-3 py-2 border-b"
        >
          <Checkbox class="" />
          <div
            v-for="column in columns"
            :key="column.key"
            class="text-base text-gray-900 truncate"
            :class="[column.size, column.align]"
          >
            {{ row[column.key] }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { FeatherIcon, Dropdown, Checkbox } from 'frappe-ui'
import SortIcon from './Icons/SortIcon.vue'
import FilterIcon from './Icons/FilterIcon.vue'
import { ref } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true,
  },
  columns: {
    type: Array,
    default: [],
  },
  rows: {
    type: Array,
    default: [],
  },
})

const currentView = ref({
  label: 'List',
  icon: 'list',
})

const viewsDropdownOptions = [
  {
    label: 'List',
    icon: 'list',
    onClick() {
      currentView.value = {
        label: 'List',
        icon: 'list',
      }
    },
  },
  {
    label: 'Table',
    icon: 'grid',
    onClick() {
      currentView.value = {
        label: 'Table',
        icon: 'grid',
      }
    },
  },
  {
    label: 'Calender',
    icon: 'calendar',
    onClick() {
      currentView.value = {
        label: 'Calender',
        icon: 'calendar',
      }
    },
  },
  {
    label: 'Board',
    icon: 'columns',
    onClick() {
      currentView.value = {
        label: 'Board',
        icon: 'columns',
      }
    },
  },
]
</script>
