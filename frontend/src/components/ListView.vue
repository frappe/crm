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
            class="flex items-center space-x-2.5"
            :class="[column.size, column.align]"
          >
            <div v-if="column.type === 'user'">
              <Avatar
                v-if="getValue(row[column.key])"
                class="flex items-center"
                :image="getValue(row[column.key]).image"
                :label="getValue(row[column.key]).label"
                size="md"
              />
            </div>
            <div v-else-if="column.type === 'logo'">
              <Avatar
                class="flex items-center"
                :label="getValue(row[column.key]).label"
                size="md"
                shape="square"
              />
            </div>
            <div v-else-if="column.type === 'status'">
              <IndicatorIcon />
            </div>
            <div class="text-base text-gray-900 truncate">
              {{ getValue(row[column.key]).label }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { FeatherIcon, Dropdown, Checkbox, Avatar } from 'frappe-ui'
import SortIcon from './Icons/SortIcon.vue'
import FilterIcon from './Icons/FilterIcon.vue'
import IndicatorIcon from './Icons/IndicatorIcon.vue'
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

function getValue(value) {
  if (typeof value === 'object') {
    value.label = value.full_name
    value.image = value.user_image
    return value
  }
  return {
    label: value,
  }
}
</script>
