<template>
  <div v-if="show" class="w-[352px] border-l">
    <div
      class="flex items-center justify-between p-4.5 text-ink-gray-7 text-lg font-medium"
    >
      <div
        class="flex items-center gap-x-2"
        :class="mode == 'edit' && 'cursor-pointer hover:text-ink-gray-8'"
        @click="mode == 'edit' && details()"
      >
        <LucideChevronLeft v-if="mode == 'edit'" class="size-4" />
        {{ __(title) }}
      </div>
      <div class="flex items-center gap-x-1">
        <Button v-if="mode == 'details'" variant="ghost" @click="editDetails">
          <template #icon>
            <EditIcon class="size-4" />
          </template>
        </Button>
        <Button
          v-if="mode === 'edit' || mode === 'details'"
          icon="trash-2"
          variant="ghost"
          @click="deleteEvent"
        />
        <Dropdown
          v-if="mode === 'edit' || mode === 'details'"
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
        <Button icon="x" variant="ghost" @click="close" />
      </div>
    </div>
    <div v-if="mode !== 'details'" class="text-base">
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
            <Button variant="solid" class="w-full" @click="saveEvent">
              {{
                mode === 'edit'
                  ? __('Save')
                  : mode === 'duplicate'
                    ? __('Duplicate event')
                    : __('Create event')
              }}
            </Button>
          </div>

          <ErrorMessage :message="error" />
        </div>
      </div>
    </div>
    <div v-else class="text-base">
      <div class="flex items-start gap-2 px-4.5 py-3 pb-0">
        <div
          class="mx-0.5 my-[5px] size-2.5 rounded-full cursor-pointer"
          :style="{
            backgroundColor: event.color || '#30A66D',
          }"
        />
        <div class="flex flex-col gap-[3px]">
          <div class="text-ink-gray-8 font-semibold text-xl">
            {{ event.title || __('(No title)') }}
          </div>
          <div class="text-ink-gray-6 text-p-base">{{ formattedDateTime }}</div>
        </div>
      </div>
      <div
        v-if="event.description && event.description !== '<p></p>'"
        class="mx-4.5 my-2.5 border-t border-outline-gray-1"
      />
      <div v-if="event.description && event.description !== '<p></p>'">
        <div class="flex gap-2 items-center text-ink-gray-7 px-4.5 py-1">
          <DescriptionIcon class="size-4" />
          {{ __('Description') }}
        </div>
        <div
          class="px-4.5 py-2 text-ink-gray-7 text-p-base"
          v-html="event.description"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import DescriptionIcon from '@/components/Icons/DescriptionIcon.vue'
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
  mode: {
    type: String,
    default: 'details',
  },
})

const emit = defineEmits(['save', 'delete', 'details', 'close', 'edit'])

const show = defineModel()

const title = ref('New event')
const _event = ref({})

const eventTitle = ref(null)
const error = ref(null)

watch(
  () => props.event,
  (newEvent) => {
    error.value = null

    if (props.mode === 'details') {
      title.value = 'Event details'
    } else if (props.mode === 'edit') {
      title.value = 'Editing event'
    } else if (props.mode === 'create') {
      title.value = 'New event'
    } else {
      title.value = 'Duplicate event'
    }

    nextTick(() => {
      if (props.mode === 'create') {
        _event.value.fromDate = newEvent.fromDate
        _event.value.toDate = newEvent.toDate
        _event.value.fromTime = newEvent.fromTime
        _event.value.toTime = newEvent.toTime
      } else {
        _event.value = { ...newEvent }
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

function editDetails() {
  emit('edit', _event.value)
}

function duplicateEvent() {
  emit('duplicate', _event.value)
}

function deleteEvent() {
  emit('delete', _event.value.id)
}

function details() {
  emit('details', _event.value)
}

function close() {
  show.value = false
  activeEvent.value = ''
  emit('close', _event.value)
}

const formattedDateTime = computed(() => {
  if (props.event.isFullDay) {
    return `${__('All day')} - ${dayjs(props.event.fromDateTime).format('ddd, D MMM YYYY')}`
  }

  const start = dayjs(props.event.fromDateTime)
  const end = dayjs(props.event.toDateTime)
  return `${start.format('h:mm a')} - ${end.format('h:mm a')} ${start.format('ddd, D MMM YYYY')}`
})

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
