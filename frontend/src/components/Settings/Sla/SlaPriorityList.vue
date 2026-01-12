<template>
  <div class="rounded-md border px-2 border-outline-gray-2 text-sm">
    <div
      class="grid p-3 px-4 items-center"
      :style="{
        gridTemplateColumns: getGridTemplateColumnsForTable(columns),
      }"
      v-if="slaData.priorities?.length !== 0"
    >
      <div
        v-for="column in columns"
        :key="column.key"
        class="text-gray-600 overflow-hidden whitespace-nowrap text-ellipsis"
        :class="{
          'ml-2':
            column.key === 'priority' || column.key === 'first_response_time',
        }"
      >
        {{ column.label }}
        <span v-if="column.isRequired" class="text-red-500">*</span>
      </div>
    </div>
    <hr v-if="slaData.priorities?.length !== 0" class="border-outline-gray-2" />
    <div v-for="(row, index) in slaData.priorities" :key="row.priority">
      <div
        class="grid gap-2 py-3.5 px-4 items-center"
        :style="{
          gridTemplateColumns: getGridTemplateColumnsForTable(columns),
        }"
      >
        <div
          v-for="column in columns"
          :key="column.key"
          class="w-full overflow-hidden whitespace-nowrap text-ellipsis"
        >
          <div v-if="column.key === 'default_priority'">
            <Checkbox
              v-model="row.default_priority"
              @update:modelValue="(e) => onDefaultPriorityChange(row, e)"
            />
          </div>
          <div v-else-if="column.key === 'first_response_time'">
            <Popover>
              <template #target="{ togglePopover }">
                <div
                  @click="togglePopover()"
                  class="min-h-7 w-full cursor-pointer select-none leading-5 p-1 px-2 hover:bg-surface-gray-2 rounded"
                >
                  {{ formatTimeHMS(row[column.key]) }}
                </div>
              </template>
              <template #body>
                <div class="absolute bg-surface-modal top-2 rounded">
                  <DurationPicker v-model="row[column.key]" />
                </div>
              </template>
            </Popover>
          </div>
          <div v-else class="ml-2">
            <select
              class="w-full h-7 text-base hover:bg-surface-gray-3 rounded-md p-0 pl-2 pr-5 bg-transparent -ml-2 border-0 text-ink-gray-8 focus-visible:!ring-0 bg-none truncate"
              v-model="row[column.key]"
            >
              <option
                v-for="option in priorityOptions"
                :key="option.value"
                :value="option.value"
                class="bg-surface-gray-3"
              >
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="flex justify-end">
          <Dropdown placement="right" :options="dropdownOptions(row)">
            <Button
              icon="more-horizontal"
              variant="ghost"
              @click="isConfirmingDelete = false"
            />
          </Dropdown>
        </div>
      </div>
      <hr
        v-if="!(index === slaData.priorities.length - 1)"
        class="border-outline-gray-2"
      />
    </div>
    <div
      v-if="slaData.priorities?.length === 0"
      class="text-center p-4 text-gray-600"
    >
      {{ __('No priorities in the list') }}
    </div>
  </div>
  <div
    class="flex items-center justify-between mt-2.5"
    v-if="
      slaData.priorities.length !== priorityOptions.length ||
      slaDataErrors.default_priority ||
      slaDataErrors.priorities
    "
  >
    <div>
      <Button
        v-if="slaData.priorities.length !== priorityOptions.length"
        variant="subtle"
        :label="__('Add row')"
        @click="addRow"
        icon-left="plus"
      />
    </div>
    <ErrorMessage
      :message="slaDataErrors.default_priority || slaDataErrors.priorities"
    />
  </div>
  <EditResponseResolutionModal v-model="dialog" :priority="priorityData" />
</template>

<script setup>
import {
  Button,
  Checkbox,
  createResource,
  Dropdown,
  ErrorMessage,
  Popover,
  toast,
} from 'frappe-ui'
import { slaData, slaDataErrors, validateSlaData } from './utils'
import {
  ConfirmDelete,
  formatTimeHMS,
  getGridTemplateColumnsForTable,
} from '../../../utils'
import { computed, inject, provide, reactive, ref } from 'vue'
import EditResponseResolutionModal from './EditResponseResolutionModal.vue'
import DurationPicker from '../../Controls/DurationPicker.vue'
import { watchDebounced } from '@vueuse/core'

const step = inject('step')
const isConfirmingDelete = ref(false)
const dialog = ref(false)
const priorityData = ref({
  priority: '',
  first_response_time: '',
  default_priority: '',
})

const priorityOptions = reactive([])
provide('priorityOptions', priorityOptions)

createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'CRM Communication Status',
    fields: ['name'],
  },
  auto: true,
  onSuccess(data) {
    priorityOptions.push(
      ...data.map((p) => {
        return {
          label: p.name,
          value: p.name,
        }
      }),
    )
    if (!step.value.data) {
      slaData.value.priorities = priorityOptions.map((p, index) => {
        return {
          priority: p.value,
          first_response_time: 60 * 60,
          default_priority: index === 0,
        }
      })
    }
  },
})

const columns = computed(() => [
  {
    label: __('Priority'),
    key: 'priority',
    isRequired: true,
  },
  {
    label: __('First response time'),
    key: 'first_response_time',
    isRequired: true,
  },
  {
    label: __('Default priority'),
    key: 'default_priority',
  },
])

const dropdownOptions = (priority) => [
  {
    label: __('Edit'),
    onClick: () => editItem(priority),
    icon: 'edit',
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteItem(priority),
    isConfirmingDelete,
  }),
]

const addRow = () => {
  const existingPriorities = slaData.value.priorities.map((p) => p.priority)
  const availablePriorities = priorityOptions.filter(
    (p) => !existingPriorities.includes(p.value),
  )

  if (availablePriorities.length === 0) {
    toast.error(__('All available priorities have already been added'))
    return
  }

  const newPriority = availablePriorities[0].value

  slaData.value.priorities.push({
    priority: newPriority,
    first_response_time: 60 * 60,
    default_priority: slaData.value.priorities.length === 0,
  })
}

const deleteItem = (priority) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true
    return
  }

  slaData.value.priorities.splice(slaData.value.priorities.indexOf(priority), 1)
}

const editItem = (priority) => {
  dialog.value = true
  priorityData.value = {
    priority: priority.priority,
    first_response_time: priority.first_response_time,
    default_priority: priority.default_priority,
  }
}

const onDefaultPriorityChange = (priority, defaultPriority) => {
  slaData.value.priorities.forEach((p) => {
    p.default_priority = false
  })
  priority.default_priority = defaultPriority
}

watchDebounced(
  () => [...slaData.value.priorities],
  (d) => {
    validateSlaData('priorities')
  },
  { deep: true, debounce: 300 },
)
</script>
