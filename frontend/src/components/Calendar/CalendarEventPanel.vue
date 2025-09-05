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
        <ShortcutTooltip
          v-if="mode == 'details'"
          :label="__('Edit event')"
          combo="Enter"
        >
          <Button :icon="EditIcon" variant="ghost" @click="editDetails" />
        </ShortcutTooltip>
        <ShortcutTooltip
          v-if="mode === 'edit' || mode === 'details'"
          :label="__('Delete event')"
          combo="Delete"
          :alt-combos="['Backspace']"
        >
          <Button icon="trash-2" variant="ghost" @click="deleteEvent" />
        </ShortcutTooltip>
        <ShortcutTooltip
          v-if="mode === 'edit' || mode === 'details'"
          :label="__('Duplicate event')"
          combo="Mod+D"
        >
          <Button icon="copy" variant="ghost" @click="duplicateEvent" />
        </ShortcutTooltip>
        <ShortcutTooltip :label="__('Close panel')" combo="Esc">
          <Button icon="x" variant="ghost" @click="close" />
        </ShortcutTooltip>
      </div>
    </div>

    <!-- Event Details -->
    <div v-if="mode == 'details'" class="flex flex-col overflow-y-auto">
      <div
        class="flex items-start gap-2 px-4.5 py-3 pb-0"
        @dblclick="editDetails"
      >
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
            :tooltip="__('Owner: {0}', [_event.owner?.label])"
          >
            <template #default>
              <div class="flex flex-col justify-start items-start text-sm">
                <div>{{ _event.owner?.label }}</div>
                <div class="text-ink-gray-5">{{ __('Organizer') }}</div>
              </div>
            </template>
            <template #prefix>
              <UserAvatar :user="_event.owner?.value" class="-ml-1 !size-5" />
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
          @keyup.enter="saveEvent"
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
            :filters="
              _event.referenceDoctype === 'CRM Lead' ? { converted: 0 } : {}
            "
            variant="outline"
            @update:model-value="sync"
          />
        </div>
      </div>
      <div class="mx-4.5 my-2.5 border-t border-outline-gray-1" />
      <Attendee
        class="px-4.5 py-[7px]"
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
          :loading="
            mode === 'edit' ? events.setValue.loading : events.insert.loading
          "
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
import { globalStore } from '@/stores/global'
import { validateEmail } from '@/utils'
import {
  normalizeParticipants,
  buildEndTimeOptions,
  computeAutoToTime,
  validateTimeRange,
  parseEventDoc,
} from '@/composables/event'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import {
  TextInput,
  Switch,
  DatePicker,
  TimePicker,
  TextEditor,
  ErrorMessage,
  Dropdown,
  dayjs,
  CalendarColorMap as colorMap,
  CalendarActiveEvent as activeEvent,
  createDocumentResource,
} from 'frappe-ui'
import ShortcutTooltip from '@/components/ShortcutTooltip.vue'
import { ref, computed, watch, h, inject } from 'vue'
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

const show = defineModel()
const event = defineModel('event')

const events = inject('events')

const _event = ref({})

const peoples = computed({
  get() {
    return _event.value.event_participants || []
  },
  set(list) {
    _event.value.event_participants = normalizeParticipants(list)
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
  ([mode, event], [oldMode, oldEvent]) => {
    error.value = null
    focusOnTitle()
    fetchEvent(oldMode)
  },
  { immediate: true },
)

function fetchEvent(oldMode) {
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
        _event.value = parseEventDoc(data)
        oldEvent.value = { ..._event.value }
      },
    })
    if (eventResource.value.doc && !event.value.reloadEvent) {
      _event.value = parseEventDoc(eventResource.value.doc)
      oldEvent.value = { ..._event.value }
    } else {
      eventResource.value.reload()
    }
  } else {
    _event.value = event.value

    if (oldMode !== props.mode) {
      oldEvent.value = { ...event.value }
    }

    if (event.value.id === 'duplicate-event' && oldMode !== 'duplicate') {
      _event.value.title = _event.value.title + ' (Copy)'
    }
  }
  showAllParticipants.value = false
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
  } else {
    sync()
  }
}

function saveEvent() {
  if (!dirty.value) return

  error.value = null
  if (!_event.value.title) {
    error.value = __('Title is required')
    eventTitle.value.el.focus()
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

  oldEvent.value = { ..._event.value }
  sync()
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
      if (['new-event', 'duplicate-event'].includes(_event.value.id)) _close()
    })
  } else {
    _close()
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

const toOptions = computed(() => buildEndTimeOptions(_event.value.fromTime))

function updateEvent(_e) {
  Object.assign(_event.value, _e)
}

defineExpose({ updateEvent })

// Keyboard shortcuts
useKeyboardShortcuts({
  active: () => show.value,
  shortcuts: [
    { keys: 'Escape', action: () => close() },
    {
      keys: 'Enter',
      guard: () =>
        ['details', 'edit'].includes(props.mode) && props.mode === 'details',
      action: () => editDetails(),
    },
    {
      keys: ['Delete', 'Backspace'],
      guard: () => ['details', 'edit'].includes(props.mode),
      action: () => deleteEvent(),
    },
    {
      match: (e) =>
        ['details', 'edit'].includes(props.mode) &&
        (e.metaKey || e.ctrlKey) &&
        !e.shiftKey &&
        !e.altKey &&
        e.key.toLowerCase() === 'd',
      action: () => duplicateEvent(),
    },
  ],
})
</script>
