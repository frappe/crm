<template>
  <div v-if="show" class="w-[352px] border-l">
    <div
      class="flex items-center justify-between p-4.5 text-ink-gray-7 text-lg font-medium"
    >
      <div>{{ __(title) }}</div>
      <div class="flex items-center gap-x-2">
        <Dropdown
          v-if="event.id"
          :options="[
            {
              label: __('Delete'),
              value: 'delete',
              icon: 'trash-2',
              onClick: deleteEvent,
            },
          ]"
        >
          <Button variant="ghost" icon="more-horizontal" />
        </Dropdown>
        <Button icon="x" variant="ghost" @click="show = false" />
      </div>
    </div>
    <div class="text-base">
      <div>
        <div class="px-4.5 py-3">
          <TextInput
            ref="eventTitle"
            v-model="_event.title"
            :debounce="500"
            :placeholder="__('Event title')"
          >
            <template #prefix>
              <div
                class="ml-0.5 bg-surface-blue-3 size-2 rounded-full cursor-pointer"
              />
            </template>
          </TextInput>
        </div>
        <div class="flex justify-between py-2.5 px-4.5 text-ink-gray-6">
          <div class="flex items-center">
            <Switch v-model="_event.isFullDay" />
            <div class="ml-2">
              {{ __('All day') }}
            </div>
          </div>
          <div class="flex items-center gap-1.5 text-ink-gray-5">
            <LucideEarth class="size-4" />
            {{ __('GMT+5:30') }}
          </div>
        </div>
        <div
          class="flex items-center justify-between px-4.5 py-[7px] text-ink-gray-7"
        >
          <div class="">{{ __('From') }}</div>
          <div class="flex items-center gap-x-2">
            <DatePicker
              :class="[_event.isFullDay ? '[&_input]:w-[216px]' : 'max-w-28']"
              variant="outline"
              :value="_event.fromDate"
              :formatter="(date) => getFormat(date, 'MMM D, YYYY')"
              :placeholder="__('Start Date')"
              @update:modelValue="(date) => updateDate(date, true)"
            />
            <TimePicker
              v-if="!_event.isFullDay"
              class="max-w-24"
              variant="outline"
              :value="_event.fromTime"
              :placeholder="__('Start Time')"
              @update:modelValue="(time) => updateTime(time, true)"
            />
          </div>
        </div>
        <div
          class="flex items-center justify-between px-4.5 py-[7px] text-ink-gray-7"
        >
          <div class="w-20">{{ __('To') }}</div>
          <div class="flex items-center gap-x-2">
            <DatePicker
              :class="[_event.isFullDay ? '[&_input]:w-[216px]' : 'max-w-28']"
              variant="outline"
              :value="_event.toDate"
              :formatter="(date) => getFormat(date, 'MMM D, YYYY')"
              :placeholder="__('End Date')"
              @update:modelValue="(date) => updateDate(date)"
            />
            <TimePicker
              v-if="!_event.isFullDay"
              class="max-w-24"
              variant="outline"
              :value="_event.toTime"
              :placeholder="__('End Time')"
              @update:modelValue="(time) => updateTime(time)"
            />
          </div>
        </div>
        <div class="mx-4.5 my-2.5 border-t" />
        <div class="px-4.5 py-3">
          <div class="flex items-center gap-x-2 border rounded py-1">
            <TextEditor
              editor-class="!prose-sm overflow-auto min-h-[20px] max-h-32 px-2 rounded placeholder-ink-gray-4 focus:bg-surface-white focus:ring-0 text-ink-gray-8 transition-colors"
              :bubbleMenu="true"
              :content="_event.description"
              @change="(val) => (_event.description = val)"
              :placeholder="__('Add description')"
            />
          </div>
          <div class="my-3">
            <Button
              variant="solid"
              class="w-full"
              :disabled="!dirty"
              @click="saveEvent"
            >
              {{ _event.id ? __('Save') : __('Create event') }}
            </Button>
          </div>

          <ErrorMessage :message="error" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import TimePicker from './TimePicker.vue'
import { getFormat } from '@/utils'
import {
  TextInput,
  Switch,
  DatePicker,
  TextEditor,
  ErrorMessage,
  Dropdown,
  dayjs,
} from 'frappe-ui'
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  event: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['save', 'delete'])

const show = defineModel()

const title = ref('New event')
const _event = ref({})

const eventTitle = ref(null)
const error = ref(null)

const dirty = computed(() => {
  return JSON.stringify(_event.value) !== JSON.stringify(props.event)
})

watch(
  () => props.event,
  (newEvent) => {
    error.value = null

    if (newEvent && newEvent.id) {
      title.value = 'Event details'
    } else {
      title.value = 'New event'
    }

    nextTick(() => (_event.value = { ...newEvent }))
    setTimeout(() => eventTitle.value?.el?.focus(), 100)
  },
  { immediate: true },
)

function updateDate(d, fromDate = false) {
  error.value = null
  let oldTo = _event.value.toDate || _event.value.fromDate

  if (fromDate) {
    _event.value.fromDate = d
    if (!_event.value.toDate) {
      _event.value.toDate = d
    }
  } else {
    _event.value.toDate = d
  }

  if (_event.value.toDate && _event.value.fromDate) {
    const diff = dayjs(_event.value.toDate).diff(
      dayjs(_event.value.fromDate),
      'day',
    )

    if (diff < 0) {
      _event.value.toDate = oldTo
      error.value = __('End date should be after start date')
      return
    }
  }
}

function updateTime(t, fromTime = false) {
  error.value = null
  let oldTo = _event.value.toTime || _event.value.fromTime

  if (fromTime) {
    _event.value.fromTime = t
    if (!_event.value.toTime) {
      const hour = parseInt(t.split(':')[0])
      const minute = parseInt(t.split(':')[1])
      _event.value.toTime = `${hour + 1}:${minute}`
    }
  } else {
    _event.value.toTime = t
  }

  if (_event.value.toTime && _event.value.fromTime) {
    const diff = dayjs(_event.value.toDate + ' ' + _event.value.toTime).diff(
      dayjs(_event.value.fromDate + ' ' + _event.value.fromTime),
      'minute',
    )

    if (diff < 0) {
      _event.value.toTime = oldTo
      error.value = __('End time should be after start time')
      return
    }
  }
}

function saveEvent() {
  error.value = null
  if (!_event.value.title) {
    error.value = __('Title is required')
    eventTitle.value.el.focus()
    return
  }

  _event.value.fromDateTime =
    _event.value.fromDate + ' ' + _event.value.fromTime
  _event.value.toDateTime = _event.value.toDate + ' ' + _event.value.toTime

  emit('save', _event.value)
}

function deleteEvent() {
  emit('delete', _event.value.id)
}
</script>
