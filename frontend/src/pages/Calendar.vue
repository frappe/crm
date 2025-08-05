<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Calendar" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Create')" @click="showEventPanelArea">
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
      :onCellDblClick="showEventPanelArea"
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
      @save="saveEvent"
      @delete="deleteEvent"
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
import { ref } from 'vue'

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
    onSuccess: async () => {
      await events.reload()
      calendar.value.reloadEvents()
    },
  },
  delete: {
    onSuccess: async () => {
      await events.reload()
      calendar.value.reloadEvents()
    },
  },
  setValue: {
    onSuccess: async () => {
      await events.reload()
      calendar.value.reloadEvents()
    },
  },
})

function saveEvent(_event) {
  _event.id ? updateEvent(_event) : createEvent(_event)
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
        activeEvent.value = e.name
      },
    },
  )
}

function updateEvent(_event) {
  if (!_event.id) return

  events.setValue.submit({
    name: _event.id,
    subject: _event.title,
    description: _event.description,
    starts_on: _event.fromDateTime,
    ends_on: _event.toDateTime,
    all_day: _event.isFullDay,
    event_type: _event.eventType,
    color: _event.color,
  })

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
          activeEvent.value = ''
          close()
        },
      },
    ],
  })
}

const showEventPanel = ref(false)
const event = ref({})

function showDetails(e) {}

function editDetails(e) {
  showEventPanel.value = true
  event.value = { ...e.calendarEvent }

  activeEvent.value = e.calendarEvent.id
}

function showEventPanelArea(e) {
  let [fromTime, toTime] = getFromToTime(e.time)

  let fromDate = dayjs(e.date).format('YYYY-MM-DD')

  activeEvent.value = ''
  showEventPanel.value = true
  event.value = {
    title: '',
    description: '',
    date: fromDate,
    fromDate: fromDate,
    toDate: fromDate,
    fromTime,
    toTime,
    isFullDay: false,
    eventType: 'Public',
  }
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
