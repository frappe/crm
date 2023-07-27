<template>
  <div id="header" class="flex justify-between items-center px-5 py-4">
    <div class="left flex space-x-2">
      <h1 class="font-semibold text-xl">{{ title }}s</h1>
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
          <Button :label="currentView.label">
            <template #prefix
              ><FeatherIcon :name="currentView.icon" class="h-4"
            /></template>
            <template #suffix
              ><FeatherIcon
                :name="open ? 'chevron-up' : 'chevron-down'"
                class="h-4"
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
        <Checkbox
          class="[&>input]:duration-300 [&>input]:cursor-pointer"
          :modelValue="allRowsSelected"
          @click="toggleAllRows"
        />
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
        <router-link
          v-for="row in rows"
          :key="row[rowKey]"
          :to="$router.currentRoute.value.path + '/' + row[rowKey]"
          class="flex space-x-4 items-center mx-2 px-3 py-2 border-b cursor-pointer transition-all duration-200 ease-in-out"
          :class="
            selections.has(row[rowKey])
              ? 'bg-gray-100 hover:bg-gray-200'
              : 'hover:bg-gray-50'
          "
        >
          <Checkbox
            :modelValue="selections.has(row[rowKey])"
            @click.stop="toggleRow(row[rowKey])"
            class="[&>input]:duration-300 [&>input]:cursor-pointer"
          />
          <div
            v-for="column in columns"
            :key="column.key"
            class="flex items-center space-x-2.5"
            :class="[column.size, column.align]"
          >
            <div v-if="column.type === 'avatar'">
              <Avatar
                v-if="getValue(row[column.key]).label"
                class="flex items-center"
                :image="getValue(row[column.key]).image"
                :label="getValue(row[column.key]).image_label"
                size="md"
              />
            </div>
            <div v-else-if="column.type === 'logo'">
              <Avatar
                v-if="getValue(row[column.key]).label"
                class="flex items-center"
                :image="getValue(row[column.key]).logo"
                :label="getValue(row[column.key]).image_label"
                size="md"
                shape="square"
              />
            </div>
            <div v-else-if="column.type === 'indicator'">
              <IndicatorIcon :class="getValue(row[column.key]).color" />
            </div>
            <div class="text-base text-gray-900 truncate">
              {{ getValue(row[column.key]).label }}
            </div>
          </div>
        </router-link>
      </div>
      <transition
        enter-active-class="duration-300 ease-out"
        enter-from-class="transform opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="transform opacity-0"
      >
        <div
          v-if="selections.size"
          class="fixed inset-x-0 bottom-6 mx-auto w-max text-base"
        >
          <div
            class="w-[596px] flex items-center space-x-3 rounded-lg bg-white px-4 py-2 shadow-2xl"
          >
            <div
              class="flex flex-1 items-center space-x-3 border-r border-gray-300 text-gray-900"
            >
              <Checkbox
                :modelValue="true"
                :disabled="true"
                class="[&>input]:text-gray-900"
              />
              <div>{{ selectedText }}</div>
            </div>
            <div class="flex items-center space-x-1">
              <Button
                class="text-gray-700"
                :disabled="allRowsSelected"
                :class="allRowsSelected ? 'cursor-not-allowed' : ''"
                variant="ghost"
                @click="toggleAllRows(true)"
              >
                Select all
              </Button>
              <Button icon="x" variant="ghost" @click="toggleAllRows(false)" />
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>
<script setup>
import { FeatherIcon, Dropdown, Checkbox, Avatar } from 'frappe-ui'
import SortIcon from './Icons/SortIcon.vue'
import FilterIcon from './Icons/FilterIcon.vue'
import IndicatorIcon from './Icons/IndicatorIcon.vue'
import { reactive, ref, computed } from 'vue'

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
  rowKey: {
    type: String,
    required: true,
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
  if (value && typeof value === 'object') {
    value.label = value.full_name || value.label
    value.image = value.image || value.user_image || value.logo
    value.image_label = value.image_label || value.label
    return value
  }
  return { label: value }
}

let selections = reactive(new Set())
let selectedText = computed(() => {
  let title = selections.size === 1 ? props.title : `${props.title}s`
  return `${selections.size} ${title} selected`
})

const allRowsSelected = computed(() => {
  if (!props.rows.length) return false
  return selections.size === props.rows.length
})

function toggleRow(row) {
  if (!selections.delete(row)) {
    selections.add(row)
  }
}

function toggleAllRows(select) {
  if (!select || allRowsSelected.value) {
    selections.clear()
    return
  }
  props.rows.forEach((row) => selections.add(row[props.rowKey]))
}
</script>
