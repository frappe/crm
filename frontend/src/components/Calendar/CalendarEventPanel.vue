<template>
  <div v-if="show" class="w-[352px] border-l">
    <div
      class="flex items-center justify-between p-4.5 text-ink-gray-7 text-lg font-medium"
    >
      <div
        class="flex items-center gap-x-2"
        :class="event.id && 'cursor-pointer hover:text-ink-gray-8'"
        @click="event.id && goToDetails()"
      >
        <LucideChevronLeft v-if="event.id" class="size-4" />
        {{ __(title) }}
      </div>
      <div class="flex items-center gap-x-1">
        <Button
          v-if="event.id"
          icon="trash-2"
          variant="ghost"
          @click="deleteEvent"
        />
        <Dropdown
          v-if="event.id"
          :options="[
            {
              label: __('Duplicate'),
              icon: 'copy',
              onClick: duplicateEvent,
            },
          ]"
        >
          <Button variant="ghost" icon="more-vertical" />
        </Dropdown>
        <Button
          icon="x"
          variant="ghost"
          @click="
            () => {
              show = false
              activeEvent = ''
            }
          "
        />
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
              <Dropdown class="ml-1" :options="colors">
                <div
                  class="ml-0.5 size-2.5 rounded-full cursor-pointer"
                  :style="{
                    backgroundColor: _event.color || '#30A66D',
                  }"
                />
              </Dropdown>
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
          <div class="">{{ __('Date') }}</div>
          <div class="flex items-center gap-x-2">
            <DatePicker
              :class="['[&_input]:w-[216px]']"
              variant="outline"
              :value="_event.fromDate"
              :formatter="(date) => getFormat(date, 'MMM D, YYYY')"
              :placeholder="__('May 1, 2025')"
              @update:modelValue="(date) => updateDate(date, true)"
            >
              <template #suffix="{ togglePopover }">
                <FeatherIcon
                  name="chevron-down"
                  class="h-4 w-4 cursor-pointer"
                  @click="togglePopover"
                />
              </template>
            </DatePicker>
          </div>
        </div>
        <div
          v-if="!_event.isFullDay"
          class="flex items-center justify-between px-4.5 py-[7px] text-ink-gray-7"
        >
          <div class="w-20">{{ __('Time') }}</div>
          <div class="flex items-center gap-x-3">
            <TimePicker
              v-if="!_event.isFullDay"
              class="max-w-[102px]"
              variant="outline"
              :value="_event.fromTime"
              :placeholder="__('Start Time')"
              @update:modelValue="(time) => updateTime(time, true)"
            >
              <template #suffix="{ togglePopover }">
                <FeatherIcon
                  name="chevron-down"
                  class="h-4 w-4 cursor-pointer"
                  @click="togglePopover"
                />
              </template>
            </TimePicker>
            <TimePicker
              class="max-w-[102px]"
              variant="outline"
              :value="_event.toTime"
              :placeholder="__('End Time')"
              @update:modelValue="(time) => updateTime(time)"
            >
              <template #suffix="{ togglePopover }">
                <FeatherIcon
                  name="chevron-down"
                  class="h-4 w-4 cursor-pointer"
                  @click="togglePopover"
                />
              </template>
            </TimePicker>
          </div>
        </div>
        <div class="mx-4.5 my-2.5 border-t border-outline-gray-1" />
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
  CalendarColorMap as colorMap,
  CalendarActiveEvent as activeEvent,
} from 'frappe-ui'
import { ref, computed, watch, nextTick, h } from 'vue'

const props = defineProps({
  event: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['save', 'delete', 'goToDetails'])

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
      title.value = 'Editing event'
    } else if (!newEvent.title) {
      title.value = 'New event'
    } else {
      title.value = 'Duplicate event'
    }

    nextTick(() => {
      _event.value = { ...newEvent }
      if (title.value == 'Duplicate event') {
        _event.value.title = `${_event.value.title} (Copy)`
      }
    })
    setTimeout(() => eventTitle.value?.el?.focus(), 100)
  },
  { immediate: true },
)

function updateDate(d) {
  _event.value.fromDate = d
  _event.value.toDate = d
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

function duplicateEvent() {
  props.event.id = ''
  title.value = 'Duplicate event'
  _event.value = { ...props.event }
  _event.value.title = `${_event.value.title} (Copy)`
  nextTick(() => eventTitle.value?.el?.focus())
}

function deleteEvent() {
  emit('delete', _event.value.id)
}

function goToDetails() {
  show.value = false
  emit('goToDetails', _event.value)
}

const colors = Object.keys(colorMap).map((color) => ({
  label: color.charAt(0).toUpperCase() + color.slice(1),
  value: colorMap[color].color,
  icon: h('div', {
    class: '!size-2.5 rounded-full',
    style: { backgroundColor: colorMap[color].color },
  }),
  onClick: () => {
    _event.value.color = colorMap[color].color
  },
}))
</script>
