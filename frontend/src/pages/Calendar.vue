<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Calendar" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Create')" @click="newEvent">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex h-screen overflow-hidden">
    <Calendar
      v-if="events.data?.length"
      class="flex-1 overflow-hidden"
      ref="calendar"
      :config="{
        defaultMode: 'Week',
        isEditMode: true,
        eventIcons: {},
        allowCustomClickEvents: true,
        redundantCellHeight: 100,
        enableShortcuts: false,
        noBorder: true,
      }"
      :events="events.data"
      @create="(event) => createEvent(event)"
      @update="(event) => updateEvent(event)"
      @delete="(eventID) => deleteEvent(eventID)"
      :onClick="showDetails"
      :onDblClick="editDetails"
      :onCellClick="newEvent"
    >
      <template
        #header="{
          currentMonthYear,
          enabledModes,
          activeView,
          decrement,
          increment,
          updateActiveView,
        }"
      >
        <div class="my-4 mx-5 flex justify-between">
          <!-- left side  -->
          <!-- Year, Month -->
          <span class="text-lg font-medium text-ink-gray-8">
            {{ currentMonthYear }}
          </span>
          <!-- right side -->
          <!-- actions buttons for calendar -->
          <div class="flex gap-x-1">
            <!-- Increment and Decrement Button-->

            <Button
              @click="decrement()"
              variant="ghost"
              class="h-4 w-4"
              icon="chevron-left"
            />
            <Button
              @click="increment()"
              variant="ghost"
              class="h-4 w-4"
              icon="chevron-right"
            />

            <!--  View change button, default is months or can be set via props!  -->
            <TabButtons
              :buttons="enabledModes"
              class="ml-2"
              :modelValue="activeView"
              @update:modelValue="updateActiveView($event)"
            />
          </div>
        </div>
      </template>
      <template #daily-header="{ parseDateWithDay, currentDate }">
        <p class="ml-4 pb-2 text-base text-ink-gray-6">
          {{ parseDateWithDay(currentDate) }}
        </p>
      </template>
    </Calendar>

    <CalendarEventPanel
      v-if="showEventPanel"
      v-model="showEventPanel"
      :event="event"
      :mode="mode"
      @save="saveEvent"
      @edit="editDetails"
      @delete="deleteEvent"
      @duplicate="duplicateEvent"
      @details="showDetails"
      @close="close"
    />
  </div>
</template>
<script setup>
import CalendarEventPanel from '@/components/Calendar/CalendarEventPanel.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { sessionStore } from '@/stores/session'
import { globalStore } from '@/stores/global'
import {
  Calendar,
  createListResource,
  TabButtons,
  dayjs,
  CalendarActiveEvent as activeEvent,
} from 'frappe-ui'
import { onMounted, ref } from 'vue'

const { user } = sessionStore()
const { $dialog } = globalStore()

const calendar = ref(null)

const events = createListResource({
  doctype: 'Event',
  cache: ['calendar', user],
  fields: [
    'name',
    'status',
    'subject',
    'description',
    'starts_on',
    'ends_on',
    'all_day',
    'event_type',
    'color',
  ],
  filters: { status: 'Open', owner: user },
  auto: true,
  transform: (data) => {
    return data.map((event) => ({
      id: event.name,
      title: event.subject,
      description: event.description,
      status: event.status,
      fromDate: event.starts_on,
      toDate: event.ends_on,
      isFullDay: event.all_day,
      eventType: event.event_type,
      color: event.color,
    }))
  },
  insert: {
    onSuccess: () => events.reload(),
  },
  delete: {
    onSuccess: () => events.reload(),
  },
  setValue: {
    onSuccess: () => events.reload(),
  },
})

function saveEvent(_event) {
  if (
    !_event.id ||
    _event.id === 'new-event' ||
    _event.id === 'duplicate-event'
  ) {
    createEvent(_event)
  } else {
    updateEvent(_event)
  }
}

function createEvent(_event) {
  if (!_event.title) return

  events.insert.submit(
    {
      subject: _event.title,
      description: _event.description,
      starts_on: _event.fromDateTime,
      ends_on: _event.toDateTime,
      all_day: _event.isFullDay,
      event_type: _event.eventType,
      color: _event.color,
    },
    {
      onSuccess: (e) => {
        _event.id = e.name
        event.value = _event
        showEventPanel.value = true
        activeEvent.value = e.name
        mode.value = 'details'
      },
    },
  )
}

function updateEvent(_event) {
  if (!_event.id) return

  if (!mode.value || mode.value === 'edit' || mode.value === 'details') {
    events.setValue.submit(
      {
        name: _event.id,
        subject: _event.title,
        description: _event.description,
        starts_on: _event.fromDateTime,
        ends_on: _event.toDateTime,
        all_day: _event.isFullDay,
        event_type: _event.eventType,
        color: _event.color,
      },
      {
        onSuccess: () => {
          mode.value = 'details'
        },
      },
    )
  }

  event.value = _event
}

function deleteEvent(eventID) {
  if (!eventID) return

  $dialog({
    title: __('Delete'),
    message: __('Are you sure you want to delete this event?'),
    variant: 'solid',
    theme: 'red',
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: (close) => {
          events.delete.submit(eventID)
          showEventPanel.value = false
          event.value = {}
          activeEvent.value = ''
          mode.value = ''
          close()
        },
      },
    ],
  })
}

onMounted(() => {
  activeEvent.value = ''
  mode.value = ''
  showEventPanel.value = false
})

const showEventPanel = ref(false)
const event = ref({})
const mode = ref('')

function showDetails(e) {
  let _e = e?.calendarEvent || e
  if (_e.id === 'new-event' || _e.id === 'duplicate-event') return

  events.data = events.data.filter(
    (ev) => ev.id !== 'new-event' && ev.id !== 'duplicate-event',
  )

  showEventPanel.value = true
  event.value = { ..._e }
  activeEvent.value = _e.id
  mode.value = 'details'
}

function editDetails(e) {
  let _e = e?.calendarEvent || e
  if (_e.id === 'new-event' || _e.id === 'duplicate-event') return

  events.data = events.data.filter(
    (ev) => ev.id !== 'new-event' && ev.id !== 'duplicate-event',
  )

  showEventPanel.value = true
  event.value = { ..._e }
  activeEvent.value = _e.id
  mode.value = 'edit'
}

function newEvent(e, duplicate = false) {
  events.data = events.data.filter(
    (ev) => ev.id !== 'new-event' && ev.id !== 'duplicate-event',
  )

  let fromTime = e.fromTime
  let toTime = e.toTime
  let fromDate = e.fromDate

  if (!duplicate) {
    let t = getFromToTime(e.time)
    fromTime = t[0]
    toTime = t[1]
    fromDate = dayjs(e.date).format('YYYY-MM-DD')
    e = { fromDate, fromTime, toTime }
  }

  showEventPanel.value = true

  event.value = {
    id: duplicate ? 'duplicate-event' : 'new-event',
    title: duplicate ? `${e.title} (Copy)` : '',
    description: e.description || '',
    date: fromDate,
    fromDate: fromDate,
    toDate: fromDate,
    fromTime,
    toTime,
    isFullDay: e.isFullDay,
    eventType: e.eventType || 'Public',
    color: e.color || 'green',
  }

  events.data.push({
    id: duplicate ? 'duplicate-event' : 'new-event',
    title: duplicate ? `${e.title} (Copy)` : '',
    description: e.description || '',
    status: 'Open',
    eventType: e.eventType || 'Public',
    fromDate: fromDate + ' ' + fromTime,
    toDate: fromDate + ' ' + toTime,
    color: e.color || 'green',
    isFullDay: e.isFullDay,
  })

  activeEvent.value = duplicate ? 'duplicate-event' : 'new-event'
  mode.value = duplicate ? 'duplicate' : 'create'
}

function duplicateEvent(e) {
  newEvent(e, true)
}

function close() {
  showEventPanel.value = false
  event.value = {}
  activeEvent.value = ''
  mode.value = ''

  events.data = events.data.filter(
    (ev) => ev.id !== 'new-event' && ev.id !== 'duplicate-event',
  )
}

// utils
function getFromToTime(time) {
  let currentTime = dayjs().format('HH:mm') || '00:00'
  let h = currentTime.split(':')[0]
  let m = parseInt(currentTime.split(':')[1])

  m = Math.floor(m / 15) * 15
  m = m < 10 ? '0' + m : String(m)

  let fromTime = `${h}:${m}`
  let toTime = `${parseInt(h) + 1}:${m}`

  if (
    time?.toLowerCase().includes('am') ||
    time?.toLowerCase().includes('pm')
  ) {
    // 12 hour format
    time = time.trim().replace(' ', '')
    const ampm = time.slice(-2)
    time = time.slice(0, -2)
    let hour = time

    if (ampm === 'pm' && parseInt(hour) < 12) {
      hour = parseInt(hour) + 12
    } else if (ampm === 'am' && hour == 12) {
      hour = 0
    }

    fromTime = `${hour}:00`
    toTime = `${parseInt(hour) + 1}:00`
  } else {
    // 24 hour format
    let [hour, minute] = time ? time.split(':') : [h, m]

    fromTime = `${hour}:${minute || '00'}`
    toTime = `${parseInt(hour) + 1}:${minute || '00'}`
  }

  return [fromTime, toTime]
}
</script>
