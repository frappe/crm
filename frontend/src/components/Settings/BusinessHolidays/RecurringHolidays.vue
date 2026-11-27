<template>
  <div class="rounded-5 border px-2 border-outline-gray-2 text-sm">
    <template v-if="rules.length">
      <div
        class="grid p-3 px-4 items-center text-ink-gray-5"
        :style="{ gridTemplateColumns: GRID_COLUMNS }"
      >
        <div>{{ __('Day') }}</div>
        <div>{{ __('Repetition') }}</div>
      </div>
      <hr class="border-outline-gray-2" />
    </template>
    <div v-for="(rule, index) in rules" :key="rule.day">
      <div
        class="grid gap-2 py-2.5 px-4 items-center"
        :style="{ gridTemplateColumns: GRID_COLUMNS }"
      >
        <div class="text-ink-gray-8 truncate">{{ __(rule.day) }}</div>
        <div class="text-ink-gray-8 truncate">
          {{ getRepetitionText(rule.repetition) }}
        </div>
        <div class="flex justify-end">
          <Dropdown
            align="end"
            :options="dropdownOptions(index)"
            @update:open="
              (open: boolean) => open && (isConfirmingDelete = false)
            "
          >
            <Button icon="lucide-more-horizontal" variant="ghost" />
          </Dropdown>
        </div>
      </div>
      <hr v-if="index !== rules.length - 1" class="border-outline-gray-2" />
    </div>
    <div v-if="!rules.length" class="text-center p-4 text-ink-gray-5">
      {{ __('No recurring holidays') }}
    </div>
  </div>
  <Button
    v-if="rules.length < WEEKDAYS.length"
    variant="subtle"
    class="mt-2.5"
    :label="__('Add Recurring Holiday')"
    icon-left="lucide-plus"
    @click="openRule(-1)"
  />
  <Dialog
    v-model:open="ruleDialog.show"
    size="md"
    :title="
      ruleDialog.index >= 0
        ? __('Edit Recurring Holiday')
        : __('Add Recurring Holiday')
    "
  >
    <template #default>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <FormLabel :label="__('Day')" required />
          <Select
            v-model="ruleDialog.day"
            :options="dayOptions"
            :placeholder="__('Select day')"
          />
        </div>
        <div class="flex flex-col gap-1.5">
          <FormLabel :label="__('Repetition')" required />
          <div class="grid grid-cols-2 gap-2 mt-1">
            <Checkbox
              v-model="ruleDialog.repetition.all"
              :label="__('Every week')"
              :disabled="WEEKS.some((week) => ruleDialog.repetition[week.key])"
            />
            <Checkbox
              v-for="week in WEEKS"
              :key="week.key"
              v-model="ruleDialog.repetition[week.key]"
              :label="week.label"
              :disabled="ruleDialog.repetition.all"
            />
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'The first week holds days 1 to 7 of the month, the second 8 to 14, and so on.',
              )
            }}
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button
          variant="subtle"
          :label="__('Cancel')"
          @click="ruleDialog.show = false"
        />
        <Button
          variant="solid"
          :label="ruleDialog.index >= 0 ? __('Update') : __('Add')"
          @click="saveRule()"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import {
  Button,
  Checkbox,
  Dialog,
  Dropdown,
  FormLabel,
  Select,
  toast,
} from 'frappe-ui'
import { computed, ref } from 'vue'
import { ConfirmDelete } from '@/utils'
import { holidayData, updateWeeklyOffDates } from './store'
import type { RepetitionPattern, Weekday } from './types'
import {
  emptyRepetition,
  getRepetitionText,
  hasRepetition,
  WEEKDAYS,
} from './utils'

const GRID_COLUMNS = '1fr 3fr 22px'

const WEEKS: { key: Exclude<keyof RepetitionPattern, 'all'>; label: string }[] =
  [
    { key: 'first', label: __('First week') },
    { key: 'second', label: __('Second week') },
    { key: 'third', label: __('Third week') },
    { key: 'fourth', label: __('Fourth week') },
    { key: 'fifth', label: __('Fifth week') },
  ]

const rules = computed(() => holidayData.value.recurring_holidays)

const ruleDialog = ref<{
  show: boolean
  // -1 when adding a rule.
  index: number
  day: Weekday | null
  repetition: RepetitionPattern
}>({ show: false, index: -1, day: null, repetition: emptyRepetition() })

const isConfirmingDelete = ref(false)

// One rule per weekday, so days that already have one are left out.
const dayOptions = computed(() => {
  const used = new Set(
    rules.value
      .filter((_, index) => index !== ruleDialog.value.index)
      .map((rule) => rule.day),
  )
  return WEEKDAYS.filter((day) => !used.has(day)).map((day) => ({
    label: __(day),
    value: day,
  }))
})

const dropdownOptions = (index: number) => [
  {
    label: __('Edit'),
    icon: 'lucide-edit',
    onClick: () => openRule(index),
  },
  ...ConfirmDelete({
    onConfirmDelete: () => deleteRule(index),
    isConfirmingDelete,
  }),
]

function openRule(index: number) {
  const rule = rules.value[index]
  ruleDialog.value = {
    show: true,
    index,
    day: rule?.day ?? null,
    repetition: rule ? { ...rule.repetition } : emptyRepetition(),
  }
}

function saveRule() {
  const { index, day, repetition } = ruleDialog.value
  if (!day) {
    toast.error(__('Select a day of the week'))
    return
  }
  if (!hasRepetition(repetition)) {
    toast.error(__('Select at least one week'))
    return
  }

  const rule = { day, repetition: { ...repetition } }
  if (index >= 0) {
    holidayData.value.recurring_holidays.splice(index, 1, rule)
  } else {
    holidayData.value.recurring_holidays.push(rule)
  }
  updateWeeklyOffDates()
  ruleDialog.value.show = false
}

function deleteRule(index: number) {
  holidayData.value.recurring_holidays.splice(index, 1)
  updateWeeklyOffDates()
}
</script>
