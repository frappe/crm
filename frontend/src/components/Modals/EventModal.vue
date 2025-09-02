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
              :placeholder="__('Start Time')"
              @update:modelValue="(time) => updateTime(time, true)"
            />
            <TimePicker
              v-if="!_event.isFullDay"
              class="max-w-[112px]"
              variant="outline"
              :modelValue="_event.toTime"
              :options="toOptions"
              :placeholder="__('End Time')"
              placement="bottom-end"
              @update:modelValue="(time) => updateTime(time)"
            />
          </div>
        </div>
        <div class="flex items-center">
          <div class="text-base text-ink-gray-7 w-3/12">
            {{ __('Link') }}
          </div>
          <div class="flex gap-2 w-9/12">
            <FormControl
              :class="_event.referenceDoctype ? 'w-20' : 'w-full'"
              type="select"
              :options="linkDoctypeOptions"
              v-model="_event.referenceDoctype"
              variant="outline"
              :placeholder="__('Add Lead or Deal')"
              @change="() => (_event.referenceDocname = '')"
            />
            <Link
              v-if="_event.referenceDoctype"
              class="w-full"
              v-model="_event.referenceDocname"
              :doctype="_event.referenceDoctype"
              variant="outline"
              :placeholder="
                __('Select {0}', [
                  _event.referenceDoctype == 'CRM Lead'
                    ? __('Lead')
                    : __('Deal'),
                ])
              "
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
      <div v-if="eventsResource" class="flex gap-2 justify-end">
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
            mode === 'edit'
              ? eventsResource.setValue.loading
              : eventsResource.insert.loading
          "
          @click="update"
        />
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import Link from '@/components/Controls/Link.vue'
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
  FormControl,
} from 'frappe-ui'
import { globalStore } from '@/stores/global'
import { validateEmail } from '@/utils'
import { allTimeSlots } from '@/components/Calendar/utils'
import { useEvent } from '@/composables/event'
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

const { eventsResource } = useEvent(props.doctype, props.docname)

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
  referenceDoctype: '',
  referenceDocname: '',
  event_participants: [],
})

const peoples = computed({
  get() {
    return _event.value.event_participants || []
  },
  set(list) {
    const seen = new Set()
    const out = []
    for (const a of list || []) {
      if (!a?.email || seen.has(a.email)) continue
      seen.add(a.email)
      out.push({
        email: a.email,
        reference_doctype: a.reference_doctype || 'Contact',
        reference_docname: a.reference_docname || '',
      })
    }
    _event.value.event_participants = out
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
      color: props.event.color,
      referenceDoctype: props.event.reference_doctype,
      referenceDocname: props.event.reference_docname,
      event_participants: props.event.event_participants || [],
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
      let nh = hour + 1
      let nm = minute
      if (nh >= 24) {
        nh = 23
        nm = 59
      }
      _event.value.toTime = `${String(nh).padStart(2, '0')}:${String(nm).padStart(2, '0')}`
    }
  } else {
    _event.value.toTime = t
  }

  validateFromToTime(oldTo)
}

function validateFromToTime(oldTo) {
  if (_event.value.isFullDay) return true
  if (_event.value.toTime && _event.value.fromTime) {
    const diff = dayjs(_event.value.fromDate + ' ' + _event.value.toTime).diff(
      dayjs(_event.value.fromDate + ' ' + _event.value.fromTime),
      'minute',
    )
    if (diff <= 0) {
      _event.value.toTime = oldTo
      error.value = __('End time should be after start time')
      return false
    }
  }
  return true
}

function update() {
  error.value = null
  if (!_event.value.title) {
    error.value = __('Title is required')
    title.value.el.focus()
    return
  }

  validateFromToTime(_event.value.toTime)

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
      color: _event.value.color,
      reference_doctype: props.doctype,
      reference_docname: props.docname,
      reference_doctype: _event.value.referenceDoctype || props.doctype,
      reference_docname: _event.value.referenceDocname || props.docname,
      event_participants: _event.value.event_participants,
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
      color: _event.value.color,
      reference_doctype: props.doctype,
      reference_docname: props.docname,
      reference_doctype: _event.value.referenceDoctype || props.doctype,
      reference_docname: _event.value.referenceDocname || props.docname,
      event_participants: _event.value.event_participants,
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

function formatDuration(mins) {
  // For < 1 hour show minutes, else show hours (with decimal for 15/30/45 mins)
  if (mins < 60) return __('{0} mins', [mins])
  let hours = mins / 60

  // keep hours decimal to 2 only if decimal is not 0
  if (hours % 1 !== 0 && hours % 1 !== 0.5) {
    hours = hours.toFixed(2)
  }

  if (Number.isInteger(hours)) {
    return hours === 1 ? __('1 hr') : __('{0} hrs', [hours])
  }
  // Keep decimal representation for > 1 hour fractional durations
  return `${hours} hrs`
}

const toOptions = computed(() => {
  const fromTime = _event.value.fromTime
  const timeSlots = allTimeSlots()
  if (!fromTime) return timeSlots
  const [fh, fm] = fromTime.split(':').map((n) => parseInt(n))
  const fromTotal = fh * 60 + fm
  // find first slot strictly after fromTime (even if fromTime not exactly a slot)
  const startIndex = timeSlots.findIndex((o) => o.value > fromTime)
  if (startIndex === -1) return []
  return timeSlots.slice(startIndex).map((o) => {
    const [th, tm] = o.value.split(':').map((n) => parseInt(n))
    const toTotal = th * 60 + tm
    const duration = toTotal - fromTotal
    return {
      ...o,
      label: `${o.label} (${formatDuration(duration)})`,
    }
  })
})

const linkDoctypeOptions = [
  { label: '', value: '' },
  { label: __('Lead'), value: 'CRM Lead' },
  { label: __('Deal'), value: 'CRM Deal' },
]

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
