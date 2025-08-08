<template>
  <div v-if="show" class="w-[352px] border-l text-base">
    <!-- Event Header -->
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

    <!-- Event Details -->
    <div v-if="mode == 'details'">
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

    <!-- Event create, duplicate & edit -->
    <div v-else>
      <div class="px-4.5 py-3">
        <TextInput
          ref="eventTitle"
          v-model="event.title"
          :debounce="500"
          :placeholder="__('Event title')"
        >
          <template #prefix>
            <Dropdown class="ml-1" :options="colors">
              <div
                class="ml-0.5 size-2.5 rounded-full cursor-pointer"
                :style="{
                  backgroundColor: event.color || '#30A66D',
                }"
              />
            </Dropdown>
          </template>
        </TextInput>
      </div>
      <div class="flex justify-between py-2.5 px-4.5 text-ink-gray-6">
        <div class="flex items-center">
          <Switch v-model="event.isFullDay" />
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
            :value="event.fromDate"
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
        v-if="!event.isFullDay"
        class="flex items-center justify-between px-4.5 py-[7px] text-ink-gray-7"
      >
        <div class="w-20">{{ __('Time') }}</div>
        <div class="flex items-center gap-x-3">
          <TimePicker
            v-if="!event.isFullDay"
            class="max-w-[102px]"
            variant="outline"
            :value="event.fromTime"
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
            :value="event.toTime"
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
            :content="event.description"
            @change="(val) => (event.description = val)"
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
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import DescriptionIcon from '@/components/Icons/DescriptionIcon.vue'
import TimePicker from './TimePicker.vue'
import { globalStore } from '@/stores/global'
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
import { ref, computed, watch, h } from 'vue'

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

const emit = defineEmits(['save', 'edit', 'delete', 'details', 'close'])

const { $dialog } = globalStore()

const show = defineModel()

const title = computed(() => {
  if (props.mode === 'details') return __('Event details')
  if (props.mode === 'edit') return __('Editing event')
  if (props.mode === 'create') return __('New event')
  return __('Duplicate event')
})

const eventTitle = ref(null)
const error = ref(null)

const oldEvent = ref(null)
const dirty = computed(() => {
  return JSON.stringify(oldEvent.value) !== JSON.stringify(props.event)
})

watch(
  [() => props.mode, () => props.event],
  () => {
    focusOnTitle()
    oldEvent.value = { ...props.event }
  },
  { immediate: true },
)

function focusOnTitle() {
  setTimeout(() => {
    if (['edit', 'create', 'duplicate'].includes(props.mode)) {
      eventTitle.value?.el?.focus()
    }
  }, 100)
}

function updateDate(d) {
  props.event.fromDate = d
  props.event.toDate = d
}

function updateTime(t, fromTime = false) {
  error.value = null
  let oldTo = props.event.toTime || props.event.fromTime

  if (fromTime) {
    props.event.fromTime = t
    if (!props.event.toTime) {
      const hour = parseInt(t.split(':')[0])
      const minute = parseInt(t.split(':')[1])
      props.event.toTime = `${hour + 1}:${minute}`
    }
  } else {
    props.event.toTime = t
  }

  if (props.event.toTime && props.event.fromTime) {
    const diff = dayjs(props.event.toDate + ' ' + props.event.toTime).diff(
      dayjs(props.event.fromDate + ' ' + props.event.fromTime),
      'minute',
    )

    if (diff < 0) {
      props.event.toTime = oldTo
      error.value = __('End time should be after start time')
      return
    }
  }
}

function saveEvent() {
  error.value = null
  if (!props.event.title) {
    error.value = __('Title is required')
    eventTitle.value.el.focus()
    return
  }

  oldEvent.value = { ...props.event }
  emit('save', props.event)
}

function editDetails() {
  emit('edit', props.event)
}

function duplicateEvent() {
  if (dirty.value) {
    showDiscardChangesModal(() => reset())
  } else {
    emit('duplicate', props.event)
  }
}

function deleteEvent() {
  emit('delete', props.event.id)
}

function details() {
  if (dirty.value) {
    showDiscardChangesModal(() => reset())
  } else {
    emit('details', props.event)
  }
}

function close() {
  const _close = () => {
    show.value = false
    activeEvent.value = ''
    emit('close', props.event)
  }

  if (dirty.value) {
    showDiscardChangesModal(() => {
      reset()
      if (props.event.id === 'new-event') _close()
    })
  } else {
    if (props.event.id === 'duplicate-event')
      showDiscardChangesModal(() => _close())
    else _close()
  }
}

function reset() {
  Object.assign(props.event, oldEvent.value)
}

function showDiscardChangesModal(action) {
  $dialog({
    title: __('Discard unsaved changes?'),
    message: __(
      'Are you sure you want to discard unsaved changes to this event?',
    ),
    actions: [
      {
        label: __('Cancel'),
        onClick: (close) => {
          close()
        },
      },
      {
        label: __('Discard'),
        variant: 'solid',
        onClick: (close) => {
          action()
          close()
        },
      },
    ],
  })
}

const formattedDateTime = computed(() => {
  const date = dayjs(props.event.fromDate)

  if (props.event.isFullDay) {
    return `${__('All day')} - ${date.format('ddd, D MMM YYYY')}`
  }

  const start = dayjs(props.event.fromDate + ' ' + props.event.fromTime)
  const end = dayjs(props.event.toDate + ' ' + props.event.toTime)

  return `${start.format('h:mm a')} - ${end.format('h:mm a')} ${date.format('ddd, D MMM YYYY')}`
})

const colors = Object.keys(colorMap).map((color) => ({
  label: color.charAt(0).toUpperCase() + color.slice(1),
  value: colorMap[color].color,
  icon: h('div', {
    class: '!size-2.5 rounded-full',
    style: { backgroundColor: colorMap[color].color },
  }),
  onClick: () => {
    props.event.color = colorMap[color].color
  },
}))
</script>
