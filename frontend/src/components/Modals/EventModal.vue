<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-header>
      <div class="mb-6 flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{
              mode === 'edit'
                ? __('Edit an event')
                : mode === 'duplicate'
                  ? __('Duplicate an event')
                  : __('Create an event')
            }}
          </h3>
        </div>
        <div class="flex gap-1">
          <Button v-if="mode === 'edit'" variant="ghost" @click="deleteEvent">
            <template #icon>
              <LucideTrash2 class="h-4 w-4 text-ink-gray-9" />
            </template>
          </Button>
          <Button
            v-if="mode === 'edit'"
            variant="ghost"
            @click="duplicateEvent"
          >
            <template #icon>
              <LucideCopy class="h-4 w-4 text-ink-gray-9" />
            </template>
          </Button>
          <Button variant="ghost" @click="show = false">
            <template #icon>
              <LucideX class="h-4 w-4 text-ink-gray-9" />
            </template>
          </Button>
        </div>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="flex items-center">
          <div class="text-base text-ink-gray-7 w-3/12">
            {{ __('Title') }}
          </div>
          <div class="flex gap-1 w-9/12">
            <Dropdown class="" :options="colors">
              <div
                class="flex items-center justify-center size-7 shrink-0 border border-outline-gray-2 bg-surface-white hover:border-outline-gray-3 hover:shadow-sm rounded cursor-pointer"
              >
                <div
                  class="size-2.5 rounded-full cursor-pointer"
                  :style="{
                    backgroundColor: _event.color || '#30A66D',
                  }"
                />
              </div>
            </Dropdown>
            <TextInput
              class="w-full"
              ref="title"
              size="sm"
              v-model="_event.title"
              :placeholder="__('Call with John Doe')"
              variant="outline"
              required
            />
          </div>
        </div>
        <div class="flex items-center">
          <div class="text-base text-ink-gray-7 w-3/12">
            {{ __('All day') }}
          </div>
          <Switch v-model="_event.isFullDay" />
        </div>
        <div class="border-t border-outline-gray-1" />
        <div class="flex items-center">
          <div class="text-base text-ink-gray-7 w-3/12">
            {{ __('Date & Time') }}
          </div>
          <div class="flex gap-2 w-9/12">
            <DatePicker
              :class="[_event.isFullDay ? 'w-full' : 'w-[158px]']"
              variant="outline"
              :value="_event.fromDate"
              :format="'MMM D, YYYY'"
              :placeholder="__('May 1, 2025')"
              :clearable="false"
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
            <TimePicker
              v-if="!_event.isFullDay"
              class="max-w-[112px]"
              variant="outline"
              :modelValue="_event.fromTime"
              :placeholder="__('Start time')"
              @update:modelValue="(time) => updateTime(time, true)"
            />
            <TimePicker
              v-if="!_event.isFullDay"
              class="max-w-[112px]"
              variant="outline"
              :modelValue="_event.toTime"
              :options="toOptions"
              :placeholder="__('End time')"
              placement="bottom-end"
              @update:modelValue="(time) => updateTime(time)"
            />
          </div>
        </div>
        <div class="flex items-start">
          <div class="text-base text-ink-gray-7 mt-1.5 w-3/12">
            {{ __('Attendees') }}
          </div>
          <div class="w-9/12">
            <Attendee
              v-model="peoples"
              :validate="validateEmail"
              :error-message="
                (value) => __('{0} is an invalid email address', [value])
              "
            />
          </div>
        </div>
        <div class="flex items-start">
          <div class="text-base text-ink-gray-7 mt-1.5 w-3/12">
            {{ __('Visibility') }}
          </div>
          <div class="w-9/12">
            <FormControl
              class="w-full"
              type="select"
              :options="[
                {
                  label: __('Private'),
                  value: 'Private',
                },
                {
                  label: __('Public'),
                  value: 'Public',
                },
              ]"
              v-model="_event.eventType"
              variant="outline"
              :placeholder="__('Private or Public')"
            />
          </div>
        </div>
        <div class="flex items-start">
          <div class="text-base text-ink-gray-7 mt-1.5 w-3/12">
            {{ __('Location') }}
          </div>
          <div class="w-9/12">
            <TextInput
              class="w-full"
              size="sm"
              variant="outline"
              v-model="_event.location"
              :placeholder="__('Add location')"
            />
          </div>
        </div>
        <div class="flex">
          <div class="mt-2 text-base text-ink-gray-7 w-3/12">
            {{ __('Description') }}
          </div>
          <div class="w-9/12">
            <TextEditor
              editor-class="!prose-sm overflow-auto min-h-[80px] max-h-80 py-1.5 px-2 rounded border border-outline-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-3 hover:border-outline-gray-modals hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
              :bubbleMenu="true"
              :content="_event.description"
              @change="(val) => (_event.description = val)"
              :placeholder="__('Add description.')"
            />
          </div>
        </div>
        <div class="border-t border-outline-gray-1" />
        <div class="flex">
          <div class="mt-1.5 text-base text-ink-gray-7 w-3/12">
            {{ __('Notifications') }}
          </div>
          <div class="w-9/12">
            <EventNotifications
              v-model="_event.notifications"
              :isAllDay="_event.isFullDay"
            />
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div
        v-if="eventsResource"
        class="flex w-full items-center justify-between"
      >
        <div>
          <ErrorMessage v-if="error" :message="__(error)" />
        </div>
        <div class="flex gap-2 justify-end">
          <Button :label="__('Cancel')" @click="show = false" />
          <Button
            variant="solid"
            :label="
              mode === 'edit'
                ? __('Update')
                : mode === 'duplicate'
                  ? __('Duplicate')
                  : __('Create')
            "
            :disabled="!dirty"
            :loading="
              mode === 'edit'
                ? eventsResource.setValue.loading
                : eventsResource.insert.loading
            "
            @click="update"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import EventNotifications from '@/components/Calendar/EventNotifications.vue'
import Attendee from '@/components/Calendar/Attendee.vue'
import {
  Switch,
  TextEditor,
  ErrorMessage,
  Dialog,
  DatePicker,
  TimePicker,
  dayjs,
  Dropdown,
} from 'frappe-ui'
import { globalStore } from '@/stores/global'
import { validateEmail } from '@/utils'
import {
  useEvent,
  normalizeParticipants,
  buildEndTimeOptions,
  computeAutoToTime,
  validateTimeRange,
} from '@/composables/event'
import { CalendarColorMap as colorMap } from 'frappe-ui'
import { onMounted, ref, computed, h } from 'vue'

const props = defineProps({
  event: {
    type: Object,
    default: () => ({}),
  },
  doctype: {
    type: String,
    default: '',
  },
  docname: {
    type: String,
    default: '',
  },
})

const { $dialog } = globalStore()

const show = defineModel()

const { eventsResource } = useEvent({
  doctype: props.doctype,
  docname: props.docname,
})

const title = ref(null)
const error = ref(null)
const mode = computed(() => {
  return _event.value.id == 'duplicate'
    ? 'duplicate'
    : _event.value.id
      ? 'edit'
      : 'create'
})

const oldEvent = ref({})
const _event = ref({
  title: '',
  description: '',
  fromDate: '',
  toDate: '',
  fromTime: '',
  toTime: '',
  isFullDay: false,
  eventType: 'Public',
  location: '',
  color: 'green',
  referenceDoctype: '',
  referenceDocname: '',
  event_participants: [],
  notifications: [],
})

const dirty = computed(() => {
  return JSON.stringify(_event.value) !== JSON.stringify(oldEvent.value)
})

const peoples = computed({
  get() {
    return _event.value.event_participants || []
  },
  set(list) {
    _event.value.event_participants = normalizeParticipants(list)
  },
})

onMounted(() => {
  if (props.event) {
    let start = dayjs(props.event.starts_on)
    let end = dayjs(props.event.ends_on)

    if (!props.event.name) {
      start = dayjs()
      end = dayjs().add(1, 'hour')
    }

    _event.value = {
      id: props.event.name || '',
      title: props.event.subject,
      description: props.event.description,
      fromDate: start.format('YYYY-MM-DD'),
      toDate: end.format('YYYY-MM-DD'),
      fromTime: start.format('HH:mm'),
      toTime: end.format('HH:mm'),
      isFullDay: props.event.all_day,
      eventType: props.event.event_type,
      location: props.event.location || '',
      color: props.event.color,
      referenceDoctype: props.event.reference_doctype,
      referenceDocname: props.event.reference_docname,
      event_participants: props.event.event_participants || [],
      notifications: props.event.notifications || [],
    }

    oldEvent.value = JSON.parse(JSON.stringify(_event.value))

    setTimeout(() => title.value?.el?.focus(), 100)
  }
})

function updateDate(d) {
  _event.value.fromDate = d
  _event.value.toDate = d
}

function updateTime(t, fromTime = false) {
  error.value = null
  const prevTo = _event.value.toTime
  if (fromTime) {
    _event.value.fromTime = t
    if (!_event.value.toTime || _event.value.toTime <= t) {
      _event.value.toTime = computeAutoToTime(t)
    }
  } else {
    _event.value.toTime = t
  }
  const { valid, error: err } = validateTimeRange({
    fromDate: _event.value.fromDate,
    fromTime: _event.value.fromTime,
    toTime: _event.value.toTime,
    isFullDay: _event.value.isFullDay,
  })
  if (!valid) {
    error.value = err
    _event.value.toTime = prevTo
  }
}

function update() {
  error.value = null
  if (!_event.value.title) {
    error.value = __('Title is required')
    title.value.el.focus()
    return
  }

  const { valid, error: err } = validateTimeRange({
    fromDate: _event.value.fromDate,
    fromTime: _event.value.fromTime,
    toTime: _event.value.toTime,
    isFullDay: _event.value.isFullDay,
  })
  if (!valid) {
    error.value = err
    return
  }

  if (_event.value.id && _event.value.id !== 'duplicate') {
    updateEvent()
  } else {
    createEvent()
  }
}

function createEvent() {
  eventsResource.insert.submit(
    {
      subject: _event.value.title,
      description: _event.value.description,
      starts_on: _event.value.fromDate + ' ' + _event.value.fromTime,
      ends_on: _event.value.toDate + ' ' + _event.value.toTime,
      all_day: _event.value.isFullDay || false,
      event_type: _event.value.eventType,
      location: _event.value.location || '',
      color: _event.value.color,
      reference_doctype: props.doctype,
      reference_docname: props.docname,
      event_participants: _event.value.event_participants,
      notifications: _event.value.notifications,
    },
    {
      onSuccess: async () => {
        await eventsResource.reload()
        show.value = false
      },
    },
  )
}

function updateEvent() {
  if (!_event.value.id) {
    error.value = __('Event ID is required')
    return
  }

  eventsResource.setValue.submit(
    {
      name: _event.value.id,
      subject: _event.value.title,
      description: _event.value.description,
      starts_on: _event.value.fromDate + ' ' + _event.value.fromTime,
      ends_on: _event.value.toDate + ' ' + _event.value.toTime,
      all_day: _event.value.isFullDay,
      event_type: _event.value.eventType,
      location: _event.value.location || '',
      color: _event.value.color,
      reference_doctype: props.doctype,
      reference_docname: props.docname,
      event_participants: _event.value.event_participants,
      notifications: _event.value.notifications,
    },
    {
      onSuccess: async () => {
        await eventsResource.reload()
        show.value = false
      },
    },
  )
}

function duplicateEvent() {
  if (!_event.value.id) return

  _event.value.id = 'duplicate'
  _event.value.title = _event.value.title + ' (Copy)'
  setTimeout(() => title.value?.el?.focus(), 100)
}

function deleteEvent() {
  if (!_event.value.id) return

  $dialog({
    title: __('Delete'),
    message: __('Are you sure you want to delete this event?'),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: (close) => {
          eventsResource.delete.submit(_event.value.id, {
            onSuccess: async () => {
              await eventsResource.reload()
              show.value = false
              close()
            },
          })
        },
      },
    ],
  })
}

const toOptions = computed(() => buildEndTimeOptions(_event.value.fromTime))

const colors = Object.keys(colorMap).map((c) => ({
  label: c.charAt(0).toUpperCase() + c.slice(1),
  value: colorMap[c].color,
  icon: h('div', {
    class: '!size-2.5 rounded-full',
    style: { backgroundColor: colorMap[c].color },
  }),
  onClick: () => (_event.value.color = colorMap[c].color),
}))
</script>
