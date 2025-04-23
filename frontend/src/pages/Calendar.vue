<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Calendar" />
    </template>
    <template #right-header>
      <Button variant="solid" :label="__('Create')" @click="createEvent">
        <template #prefix><FeatherIcon name="plus" class="h-4" /></template>
      </Button>
    </template>
  </LayoutHeader>
  <div class="flex h-screen flex-col overflow-hidden">
    <Calendar
      v-if="events.data?.length"
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
      :onCellDblClick="showNewModal"
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
        <p class="ml-4 pb-2 text-base font-semibold text-ink-gray-8">
          {{ parseDateWithDay(currentDate, (fullDay = true)) }}
        </p>
      </template>
    </Calendar>
    <CalendarModal
      v-model="showModal"
      v-model:event="event"
      @save="saveEvent"
      @delete="deleteEvent"
    />
  </div>
</template>
<script setup>
import CalendarModal from '@/components/Modals/CalendarModal.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { sessionStore } from '@/stores/session'
import { globalStore } from '@/stores/global'
import { Calendar, createListResource, TabButtons, dayjs } from 'frappe-ui'
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

function saveEvent(event) {
  event.id ? updateEvent(event) : createEvent(event)
}

function getFromDate(event) {
  return event.date + ' ' + (event.from_time ? event.from_time : '00:00:00')
}

function getToDate(event) {
  return event.date + ' ' + (event.to_time ? event.to_time : '00:00:00')
}

function createEvent(event) {
  if (!event.title) return

  events.insert.submit({
    subject: event.title,
    description: event.description,
    starts_on: getFromDate(event),
    ends_on: getToDate(event),
    all_day: event.isFullDay,
    event_type: event.eventType,
    color: event.color,
  })

  showModal.value = false
  event.value = {}
}

function updateEvent(event) {
  if (!event.id) return

  events.setValue.submit({
    name: event.id,
    subject: event.title,
    description: event.description,
    starts_on: getFromDate(event),
    ends_on: getToDate(event),
    all_day: event.isFullDay,
    event_type: event.eventType,
    color: event.color,
  })

  showModal.value = false
  event.value = {}
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
          close()
        },
      },
    ],
  })
}

const showModal = ref(false)
const event = ref({})

function showDetails(e) {}

function editDetails(e) {
  showModal.value = true
  event.value = { ...e.calendarEvent }
}

function showNewModal(e) {
  let [fromTime, toTime] = getFromToTime(e.time)

  showModal.value = true
  event.value = {
    title: '',
    description: '',
    date: dayjs(e.date).format('YYYY-MM-DD'),
    from_time: fromTime,
    to_time: toTime,
    isFullDay: false,
    eventType: 'Public',
  }
}

// utils
function getFromToTime(time) {
  let fromTime = '00:00'
  let toTime = '01:00'

  if (time.toLowerCase().includes('am') || time.toLowerCase().includes('pm')) {
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
    time = time.split(':')
    let [hour, minute] = time

    fromTime = `${hour}:${minute}`
    toTime = `${parseInt(hour) + 1}:${minute}`
  }

  return [fromTime, toTime]
}
</script>
