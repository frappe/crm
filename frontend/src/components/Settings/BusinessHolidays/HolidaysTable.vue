<template>
  <div class="rounded-5 border px-2 border-outline-gray-2 text-sm">
    <template v-if="holidays.length">
      <div
        class="grid p-3 px-4 items-center text-ink-gray-5"
        :style="{ gridTemplateColumns: GRID_COLUMNS }"
      >
        <div>{{ __('Date') }}</div>
        <div>{{ __('Description') }}</div>
      </div>
      <hr class="border-outline-gray-2" />
    </template>
    <div v-for="(holiday, index) in holidays" :key="holiday.date">
      <div
        class="grid gap-2 py-2.5 px-4 items-center"
        :style="{ gridTemplateColumns: GRID_COLUMNS }"
      >
        <div class="text-ink-gray-8 truncate">
          {{ formatHolidayDate(holiday.date) }}
        </div>
        <div class="text-ink-gray-8 truncate">{{ holiday.description }}</div>
        <div class="flex justify-end">
          <Dropdown
            align="end"
            :options="dropdownOptions(holiday)"
            @update:open="
              (open: boolean) => open && (isConfirmingDelete = false)
            "
          >
            <Button icon="lucide-more-horizontal" variant="ghost" />
          </Dropdown>
        </div>
      </div>
      <hr v-if="index !== holidays.length - 1" class="border-outline-gray-2" />
    </div>
    <div v-if="!holidays.length" class="text-center p-4 text-ink-gray-5">
      {{ __('No holidays added yet') }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { Button, Dropdown } from 'frappe-ui'
import { computed, ref } from 'vue'
import { ConfirmDelete } from '@/utils'
import { formatHolidayDate, holidayData, removeHoliday } from './store'
import type { Holiday } from './types'

const emit = defineEmits<{ edit: [holiday: Holiday] }>()

const GRID_COLUMNS = '1fr 3fr 22px'

const isConfirmingDelete = ref(false)

// Weekly offs are listed under Recurring Holidays instead.
const holidays = computed(() =>
  holidayData.value.holidays.filter((holiday) => !holiday.weekly_off),
)

const dropdownOptions = (holiday: Holiday) => [
  {
    label: __('Edit'),
    icon: 'lucide-edit',
    onClick: () => emit('edit', holiday),
  },
  ...ConfirmDelete({
    onConfirmDelete: () => removeHoliday(holiday),
    isConfirmingDelete,
  }),
]
</script>
