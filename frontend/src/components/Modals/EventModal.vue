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
          <TextInput
            ref="title"
            class="w-9/12"
            size="md"
            v-model="_event.title"
            :placeholder="__('Call with John Doe')"
            variant="outline"
            required
          />
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
              v-if="!_event.isFullDay"
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
        <ErrorMessage class="mt-4" v-if="error" :message="__(error)" />
      </div>
    </template>
    <template #actions>
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
          :loading="
            mode === 'edit' ? events.setValue.loading : events.insert.loading
          "
          @click="update"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import {
  Switch,
  TextEditor,
  ErrorMessage,
  Dialog,
  DatePicker,
  dayjs,
} from 'frappe-ui'
import { globalStore } from '@/stores/global'
import { onMounted, ref, computed } from 'vue'

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
const events = defineModel('events')

const title = ref(null)
const error = ref(null)
const mode = computed(() => {
  return _event.value.id == 'duplicate'
    ? 'duplicate'
    : _event.value.id
      ? 'edit'
      : 'create'
})

const _event = ref({
  title: '',
  description: '',
  fromDate: '',
  toDate: '',
  fromTime: '',
  toTime: '',
  isFullDay: false,
  eventType: 'Public',
  color: 'green',
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
      color: props.event.color,
    }

    setTimeout(() => title.value?.el?.focus(), 100)
  }
})

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

    if (diff <= 0) {
      _event.value.toTime = oldTo
      error.value = __('End time should be after start time')
      return
    }
  }
}

function update() {
  error.value = null
  if (!_event.value.title) {
    error.value = __('Title is required')
    title.value.el.focus()
    return
  }

  _event.value.id ? updateEvent() : createEvent()
}

function createEvent() {
  events.value.insert.submit(
    {
      subject: _event.value.title,
      description: _event.value.description,
      starts_on: _event.value.fromDate + ' ' + _event.value.fromTime,
      ends_on: _event.value.toDate + ' ' + _event.value.toTime,
      all_day: _event.value.isFullDay || false,
      event_type: _event.value.eventType,
      color: _event.value.color,
      reference_doctype: props.doctype,
      reference_docname: props.docname,
    },
    {
      onSuccess: async () => {
        await events.value.reload()
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

  events.value.setValue.submit(
    {
      name: _event.value.id,
      subject: _event.value.title,
      description: _event.value.description,
      starts_on: _event.value.fromDate + ' ' + _event.value.fromTime,
      ends_on: _event.value.toDate + ' ' + _event.value.toTime,
      all_day: _event.value.isFullDay,
      event_type: _event.value.eventType,
      color: _event.value.color,
      reference_doctype: props.doctype,
      reference_docname: props.docname,
    },
    {
      onSuccess: async () => {
        await events.value.reload()
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
          events.value.delete.submit(_event.value.id, {
            onSuccess: async () => {
              await events.value.reload()
              show.value = false
              close()
            },
          })
        },
      },
    ],
  })
}
</script>
