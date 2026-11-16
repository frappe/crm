<template>
  <Dropdown :options="options" align="end">
    <Button
      variant="solid"
      class="rounded-l-none border-l border-outline-gray-5"
      :tooltip="__('Schedule send')"
      :aria-label="__('Schedule send')"
      :disabled="disabled"
      icon="lucide-chevron-down"
      @pointerdown="openedAt = dayjs()"
    />
  </Dropdown>
  <Dialog
    v-model:open="showPicker"
    :title="__('Schedule send')"
    size="sm"
    :actions="[
      {
        label: __('Schedule send'),
        variant: 'solid',
        disabled: !pickedInFuture,
        onClick: schedulePicked,
      },
    ]"
  >
    <DateTimePicker
      v-model="pickedTime"
      :placeholder="__('Pick date & time')"
      :isDateUnavailable="(date) => date.isBefore(dayjs(), 'day')"
    />
    <ErrorMessage
      class="mt-2"
      :message="
        pickedTime && !pickedInFuture ? __('Pick a time in the future') : ''
      "
    />
  </Dialog>
</template>

<script setup lang="ts">
import {
  Dialog,
  DateTimePicker,
  Dropdown,
  ErrorMessage,
  dayjs,
  getConfig,
} from 'frappe-ui'
import type { Dayjs } from 'frappe-ui'
import { computed, h, ref, watch } from 'vue'

defineProps<{ disabled?: boolean }>()

// `confirmed` is set when the user already confirmed the time in the picker dialog
const emit = defineEmits<{
  schedule: [sendAfter: string, label: string, confirmed: boolean]
}>()

const localTimezone: string =
  getConfig('localTimezone') || Intl.DateTimeFormat().resolvedOptions().timeZone
const systemTimezone: string | null = getConfig('systemTimezone')

const openedAt = ref(dayjs())
const showPicker = ref(false)
const pickedTime = ref('')

watch(showPicker, (open) => {
  if (open) pickedTime.value = ''
})

// The picker shows the user's own clock, so read its value in their timezone
const pickedAt = computed(() =>
  pickedTime.value ? dayjs.tz(pickedTime.value, localTimezone) : null,
)
const pickedInFuture = computed(() => !!pickedAt.value?.isAfter(dayjs()))

function at(day: Dayjs, hour: number) {
  return day.hour(hour).minute(0).second(0)
}

const slots = [
  { label: __('Morning'), hour: 9, icon: 'lucide-sunrise' },
  { label: __('Afternoon'), hour: 13, icon: 'lucide-sun' },
  { label: __('Evening'), hour: 18, icon: 'lucide-sunset' },
]

function slotOptions(day: Dayjs, after: Dayjs) {
  return slots
    .map((slot) => ({ ...slot, time: at(day, slot.hour) }))
    .filter(({ time }) => time.isAfter(after))
    .map(({ label, icon, time }) => ({
      label,
      icon,
      slots: {
        suffix: () =>
          h('span', { class: 'text-ink-gray-5' }, time.format('h:mm A')),
      },
      onClick: () => schedule(time),
    }))
}

// Rebuilt each time the menu opens, so "today" and "tomorrow" never go stale
const options = computed(() => {
  const now = openedAt.value.tz(localTimezone)
  const today = slotOptions(now, now)
  const tomorrow = slotOptions(now.add(1, 'day'), now)
  return [
    ...(today.length ? [{ group: __('Today'), options: today }] : []),
    { group: __('Tomorrow'), options: tomorrow },
    {
      group: '',
      hideLabel: true,
      options: [
        {
          label: __('Custom date & time…'),
          onClick: () => (showPicker.value = true),
        },
      ],
    },
  ]
})

function schedule(time: Dayjs, confirmed = false) {
  const system = systemTimezone ? time.tz(systemTimezone) : time
  emit(
    'schedule',
    system.format('YYYY-MM-DD HH:mm:ss'),
    time.format('ddd, D MMM, h:mm A'),
    confirmed,
  )
}

function schedulePicked() {
  // Re-checked here: the time can pass while the dialog sits open
  if (!pickedInFuture.value) return
  showPicker.value = false
  schedule(pickedAt.value as Dayjs, true)
}
</script>
