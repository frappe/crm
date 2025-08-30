<template>
  <div v-if="show" class="flex flex-col w-[352px] text-base">
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
    <div v-if="mode == 'details'" class="flex flex-col overflow-y-auto">
      <div class="flex items-start gap-2 px-4.5 py-3 pb-0">
        <div
          class="mx-0.5 my-[5px] size-2.5 rounded-full cursor-pointer"
          :style="{
            backgroundColor: _event.color || '#30A66D',
          }"
        />
        <div class="flex flex-col gap-[3px]">
          <div class="text-ink-gray-8 font-semibold text-xl">
            {{ _event.title || __('(No title)') }}
          </div>
          <div class="text-ink-gray-6 text-p-base">{{ formattedDateTime }}</div>
        </div>
      </div>
      <div
        v-if="_event.referenceDocname"
        class="mx-4.5 my-2.5 border-t border-outline-gray-1"
      />
      <div
        v-if="_event.referenceDocname"
        class="flex items-center px-4.5 py-1 text-ink-gray-7"
      >
        <component
          :is="_event.referenceDoctype == 'CRM Lead' ? LeadsIcon : DealsIcon"
          class="size-4"
        />
        <Link
          class="[&_button]:bg-surface-white [&_button]:select-text [&_button]:text-ink-gray-7 [&_button]:cursor-text"
          v-model="_event.referenceDocname"
          :doctype="_event.referenceDoctype"
          :disabled="true"
        />
        <Button variant="ghost" @click="redirect">
          <template #icon>
            <ArrowUpRightIcon class="size-4 text-ink-gray-7" />
          </template>
        </Button>
      </div>
      <div
        v-if="peoples.length"
        class="mx-4.5 my-2.5 border-t border-outline-gray-1"
      />
      <div v-if="peoples.length" class="px-4.5 py-2">
        <div class="flex gap-3 text-ink-gray-7 mb-3">
          <PeopleIcon class="size-4" />
          <div>{{ __('{0} Attendees', [peoples.length + 1]) }}</div>
        </div>
        <div class="flex flex-col gap-2 -ml-1">
          <Button
            :key="_event.owner"
            variant="ghost"
            theme="gray"
            class="rounded-full w-fit !h-8.5 !pr-3"
            :tooltip="__('Owner: {0}', [_event.owner.label])"
          >
            <template #default>
              <div class="flex flex-col justify-start items-start text-sm">
                <div>{{ _event.owner.label }}</div>
                <div class="text-ink-gray-5">{{ __('Organizer') }}</div>
              </div>
            </template>
            <template #prefix>
              <UserAvatar :user="_event.owner.value" class="-ml-1 !size-5" />
            </template>
          </Button>
          <Button
            v-for="att in displayedPeoples"
            :key="att.email"
            :label="att.email"
            variant="ghost"
            theme="gray"
            class="rounded-full w-fit !text-sm"
            :tooltip="getTooltip(att)"
          >
            <template #prefix>
              <UserAvatar :user="att.email" class="-ml-1 !size-5" />
            </template>
          </Button>
          <Button
            v-if="!showAllParticipants && peoples.length > 2"
            variant="ghost"
            :label="__('See all participants')"
            iconLeft="more-horizontal"
            class="!justify-start w-fit"
            @click="showAllParticipants = true"
          />
          <Button
            v-else-if="showAllParticipants"
            variant="ghost"
            :label="__('Show less')"
            iconLeft="chevron-up"
            class="!justify-start w-fit"
            @click="showAllParticipants = false"
          />
        </div>
      </div>
      <div
        v-if="_event.description && _event.description !== '<p></p>'"
        class="mx-4.5 my-2.5 border-t border-outline-gray-1"
      />
      <div v-if="_event.description && _event.description !== '<p></p>'">
        <div class="flex gap-2 items-center text-ink-gray-7 px-4.5 py-1">
          <DescriptionIcon class="size-4" />
          {{ __('Description') }}
        </div>
        <div
          class="px-4.5 py-2 text-ink-gray-7 text-p-base"
          v-html="_event.description"
        />
      </div>
    </div>

    <!-- Event new, duplicate & edit -->
    <div v-else class="flex flex-col overflow-y-auto">
      <div class="flex gap-2 items-center px-4.5 py-3">
        <Dropdown class="ml-1" :options="colors">
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
          ref="eventTitle"
          class="w-full"
          variant="outline"
          v-model="_event.title"
          :debounce="500"
          :placeholder="__('Event title')"
          @change="sync"
        />
      </div>
      <div class="flex justify-between py-2.5 px-4.5 text-ink-gray-6">
        <div class="flex items-center">
          <Switch v-model="_event.isFullDay" @update:model-value="sync" />
          <div class="ml-2">
            {{ __('All day') }}
          </div>
        </div>
        <!-- <div class="flex items-center gap-1.5 text-ink-gray-5">
          <LucideEarth class="size-4" />
          {{ __('GMT+5:30') }}
        </div> -->
      </div>
      <div
        class="flex items-center justify-between px-4.5 py-[7px] text-ink-gray-7"
      >
        <div class="">{{ __('Date') }}</div>
        <div class="flex items-center gap-x-1.5">
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
        <div class="flex items-center gap-x-1.5">
          <TimePicker
            v-if="!_event.isFullDay"
            class="max-w-[105px]"
            variant="outline"
            :modelValue="_event.fromTime"
            :placeholder="__('Start Time')"
            @update:modelValue="(time) => updateTime(time, true)"
          />
          <TimePicker
            class="max-w-[105px]"
            variant="outline"
            :modelValue="_event.toTime"
            :options="toOptions"
            :placeholder="__('End Time')"
            placement="bottom-end"
            @update:modelValue="(time) => updateTime(time)"
          />
        </div>
      </div>
      <div class="mx-4.5 my-2.5 border-t border-outline-gray-1" />
      <div
        class="flex items-center justify-between px-4.5 py-[7px] text-ink-gray-7"
      >
        <div class="">{{ __('Link') }}</div>
        <div class="flex items-center gap-x-1.5">
          <FormControl
            class="w-[216px]"
            type="select"
            :options="[
              {
                label: '',
                value: '',
              },
              {
                label: __('Lead'),
                value: 'CRM Lead',
              },
              {
                label: __('Deal'),
                value: 'CRM Deal',
              },
            ]"
            v-model="_event.referenceDoctype"
            variant="outline"
            :placeholder="__('Add Lead or Deal')"
            @change="
              () => {
                _event.referenceDocname = ''
                sync()
              }
            "
          />
        </div>
      </div>
      <div
        v-if="_event.referenceDoctype"
        class="flex items-center justify-between px-4.5 py-[7px] text-ink-gray-7"
      >
        <div class="">
          {{ _event.referenceDoctype == 'CRM Lead' ? __('Lead') : __('Deal') }}
        </div>
        <div class="flex items-center gap-x-1.5">
          <Link
            class="w-[220px]"
            v-model="_event.referenceDocname"
            :doctype="_event.referenceDoctype"
            variant="outline"
            @update:model-value="sync"
          />
        </div>
      </div>
      <div class="mx-4.5 my-2.5 border-t border-outline-gray-1" />
      <Attendee
        v-model="peoples"
        :validate="validateEmail"
        :error-message="
          (value) => __('{0} is an invalid email address', [value])
        "
      />
      <div class="mx-4.5 my-2.5 border-t border-outline-gray-1" />
      <div class="px-4.5 py-3">
        <div class="flex items-center gap-x-2 border rounded py-1">
          <TextEditor
            editor-class="!prose-sm overflow-auto min-h-[22px] max-h-32 px-2.5 rounded placeholder-ink-gray-4 focus:bg-surface-white focus:ring-0 text-ink-gray-8 transition-colors"
            :bubbleMenu="true"
            :content="_event.description"
            @change="
              (val) => {
                _event.description = val
                sync()
              }
            "
            :placeholder="__('Add description')"
          />
        </div>
      </div>
    </div>

    <div v-if="mode != 'details'" class="px-4.5 py-3">
      <ErrorMessage class="my-2" :message="error" />
      <div class="w-full">
        <Button
          variant="solid"
          class="w-full"
          :disabled="!dirty"
          @click="saveEvent"
        >
          {{
            mode === 'edit'
              ? __('Save')
              : mode === 'duplicate'
                ? __('Duplicate event')
                : __('Create event')
          }}
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import PeopleIcon from '@/components/Icons/PeopleIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import Link from '@/components/Controls/Link.vue'
import EditIcon from '@/components/Icons/EditIcon.vue'
import DescriptionIcon from '@/components/Icons/DescriptionIcon.vue'
import TimePicker from '@/components/Calendar/TimePicker.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { getFormat, validateEmail } from '@/utils'
import { allTimeSlots } from '@/components/Calendar/utils'
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
  createDocumentResource,
} from 'frappe-ui'
import { ref, computed, watch, h } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  mode: {
    type: String,
    default: 'details',
  },
})

const emit = defineEmits([
  'save',
  'edit',
  'delete',
  'details',
  'close',
  'sync',
  'duplicate',
])

const router = useRouter()
const { $dialog } = globalStore()
const { getUser } = usersStore()

const show = defineModel()
const event = defineModel('event')

const _event = ref({})

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
    sync()
  },
})

const title = computed(() => {
  if (props.mode === 'details') return __('Event details')
  if (props.mode === 'edit') return __('Editing event')
  if (props.mode === 'new') return __('New event')
  return __('Duplicate event')
})

const eventTitle = ref(null)
const error = ref(null)
const showAllParticipants = ref(false)

const eventResource = ref({})

const oldEvent = ref(null)
const dirty = computed(() => {
  return JSON.stringify(oldEvent.value) !== JSON.stringify(_event.value)
})

const displayedPeoples = computed(() => {
  if (showAllParticipants.value) return peoples.value
  return peoples.value.slice(0, 2)
})

watch(
  [() => props.mode, () => event.value],
  () => {
    error.value = null
    focusOnTitle()
    fetchEvent()
  },
  { immediate: true },
)

function fetchEvent() {
  if (
    event.value.id &&
    event.value.id !== 'new-event' &&
    event.value.id !== 'duplicate-event'
  ) {
    eventResource.value = createDocumentResource({
      doctype: 'Event',
      name: event.value.id,
      fields: ['*'],
      onSuccess: (data) => {
        _event.value = parseEvent(data)
        oldEvent.value = { ..._event.value }
      },
    })
    if (eventResource.value.doc && !event.value.reloadEvent) {
      _event.value = parseEvent(eventResource.value.doc)
      oldEvent.value = { ..._event.value }
    } else {
      eventResource.value.reload()
    }
  } else {
    _event.value = event.value
    oldEvent.value = { ...event.value }
  }
  showAllParticipants.value = false
}

function parseEvent(_e) {
  return {
    id: _e.name,
    title: _e.subject,
    description: _e.description,
    status: _e.status,
    fromDate: dayjs(_e.starts_on).format('YYYY-MM-DD'),
    toDate: dayjs(_e.ends_on).format('YYYY-MM-DD'),
    fromTime: dayjs(_e.starts_on).format('HH:mm'),
    toTime: dayjs(_e.ends_on).format('HH:mm'),
    isFullDay: _e.all_day,
    eventType: _e.event_type,
    color: _e.color,
    referenceDoctype: _e.reference_doctype,
    referenceDocname: _e.reference_docname,
    event_participants: _e.event_participants || [],
    owner: {
      label: getUser(_e.owner).full_name,
      image: getUser(_e.owner).user_image,
      value: _e.owner,
    },
  }
}

function focusOnTitle() {
  setTimeout(() => {
    if (['edit', 'new', 'duplicate'].includes(props.mode)) {
      eventTitle.value?.el?.focus()
    }
  }, 100)
}

function sync() {
  emit('sync', _event.value.id, _event.value)
}

function updateDate(d) {
  _event.value.fromDate = d
  _event.value.toDate = d

  sync()
}

function updateTime(t, fromTime = false) {
  error.value = null

  if (fromTime) {
    _event.value.fromTime = t
    const hour = parseInt(t.split(':')[0])
    const minute = parseInt(t.split(':')[1])

    const computePlusHour = () => {
      let nh = hour + 1
      let nm = minute
      if (nh >= 24) {
        nh = 23
        nm = 59
      }
      return `${String(nh).padStart(2, '0')}:${String(nm).padStart(2, '0')}`
    }
    if (!_event.value.toTime) {
      _event.value.toTime = computePlusHour()
    } else if (_event.value.toTime <= t) {
      _event.value.toTime = computePlusHour()
    }
  } else {
    _event.value.toTime = t
  }

  validateFromToTime() && sync()
}

function validateFromToTime() {
  // Generic validator for start/end times before saving.
  // Returns true if valid, else sets error message and returns false.
  error.value = null
  // Full day events don't require time validation
  if (_event.value.isFullDay) return true

  // Only validate within the single start date; ignore any separate end date.
  const fromDate = _event.value.fromDate
  const fromTime = _event.value.fromTime
  const toTime = _event.value.toTime

  if (!fromTime || !toTime) {
    error.value = __('Start and end time are required')
    return false
  }

  const start = dayjs(fromDate + ' ' + fromTime)
  const end = dayjs(fromDate + ' ' + toTime)

  if (!start.isValid() || !end.isValid()) {
    error.value = __('Invalid start or end time')
    return false
  }

  if (end.diff(start, 'minute') <= 0) {
    error.value = __('End time should be after start time')
    return false
  }
  return true
}

function saveEvent() {
  error.value = null
  if (!_event.value.title) {
    error.value = __('Title is required')
    eventTitle.value.el.focus()
    return
  }

  if (!validateFromToTime()) return

  oldEvent.value = { ..._event.value }
  emit('save', _event.value)
}

function editDetails() {
  emit('edit', _event.value)
}

function duplicateEvent() {
  if (dirty.value) {
    showDiscardChangesModal(() => reset())
  } else {
    emit('duplicate', _event.value)
  }
}

function deleteEvent() {
  emit('delete', _event.value.id)
}

function details() {
  if (dirty.value) {
    showDiscardChangesModal(() => reset())
  } else {
    emit('details', _event.value)
  }
}

function close() {
  const _close = () => {
    show.value = false
    activeEvent.value = ''
    emit('close', _event.value)
  }

  if (dirty.value) {
    showDiscardChangesModal(() => {
      reset()
      if (_event.value.id === 'new-event') _close()
    })
  } else {
    if (_event.value.id === 'duplicate-event')
      showDiscardChangesModal(() => _close())
    else _close()
  }
}

function reset() {
  Object.assign(_event.value, oldEvent.value)
  sync()
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
  const date = dayjs(_event.value.fromDate)

  if (_event.value.isFullDay) {
    return `${__('All day')} - ${date.format('ddd, D MMM YYYY')}`
  }

  const start = dayjs(_event.value.fromDate + ' ' + _event.value.fromTime)
  const end = dayjs(_event.value.toDate + ' ' + _event.value.toTime)

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
    _event.value.color = colorMap[color].color
    sync()
  },
}))

function redirect() {
  if (_event.value.referenceDocname) {
    let name = _event.value.referenceDoctype === 'CRM Lead' ? 'Lead' : 'Deal'

    let params =
      _event.value.referenceDoctype == 'CRM Lead'
        ? { leadId: _event.value.referenceDocname }
        : { dealId: _event.value.referenceDocname }

    router.push({ name, params })
  }
}

function getTooltip(m) {
  if (!m) return email
  const parts = []
  if (m.reference_doctype) parts.push(m.reference_doctype)
  if (m.reference_docname) parts.push(m.reference_docname)
  return parts.length ? parts.join(': ') : email
}

function formatDuration(mins) {
  // For < 1 hour show minutes, else show hours (with decimal for 15/30/45 mins)
  if (mins < 60) return __('{0} mins', [mins])
  let hours = mins / 60

  // keep hours decimal to 2 only if decimal is not 0
  if (hours % 1 !== 0) {
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

function updateEvent(_e) {
  Object.assign(_event.value, _e)
}

defineExpose({ updateEvent })
</script>
