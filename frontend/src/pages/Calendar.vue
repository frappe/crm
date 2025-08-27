<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs routeName="Calendar" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        :label="__('Create')"
        :disabled="
          mode == 'edit' || mode == 'new-event' || mode == 'duplicate-event'
        "
        @click="newEvent"
      >
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
          currentYear,
          currentMonth,
          enabledModes,
          activeView,
          decrement,
          increment,
          updateActiveView,
          setCalendarDate,
        }"
      >
        <div class="my-4 mx-5 flex justify-between">
          <!-- left side  -->
          <!-- Month Year -->
          <div class="flex items-center">
            <DateMonthYearPicker
              :modelValue="selectedMonthDate"
              :formatter="(d) => dayjs(d).format('MMM YYYY')"
              @update:modelValue="
                (val) => onMonthYearChange(val, setCalendarDate)
              "
            />
          </div>
          <!-- right side -->
          <!-- actions buttons for calendar -->
          <div class="flex gap-x-1">
            <!-- Increment and Decrement Button -->

            <Button
              @click="
                () => {
                  decrement()
                  syncSelectedMonth(currentYear, currentMonth)
                }
              "
              variant="ghost"
              class="h-4 w-4"
              icon="chevron-left"
            />
            <Button
              @click="
                () => {
                  increment()
                  syncSelectedMonth(currentYear, currentMonth)
                }
              "
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
      @sync="syncEvent"
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
  call,
} from 'frappe-ui'
import DateMonthYearPicker from '@/components/Calendar/DateMonthYearPicker.vue'
import { onMounted, ref } from 'vue'

const { user } = sessionStore()
const { $dialog } = globalStore()

const calendar = ref(null)

const selectedMonthDate = ref(dayjs().format('YYYY-MM-DD'))

function onMonthYearChange(val = '', setCalendarDate) {
  const d = dayjs(val)
  selectedMonthDate.value = d.format('YYYY-MM-DD')

  if (setCalendarDate) {
    setCalendarDate(selectedMonthDate.value)
  } else if (calendar.value?.setCalendarDate) {
    calendar.value.setCalendarDate(selectedMonthDate.value)
  }
}

function syncSelectedMonth(year, month) {
  // Keep same day if possible; otherwise clamp to last day
  if (typeof year === 'number' && typeof month === 'number') {
    const currentDay = dayjs(selectedMonthDate.value).date()

    let tentative = dayjs(
      `${year}-${String(month + 1).padStart(2, '0')}-01`,
    ).date(currentDay)

    if (tentative.month() !== month) {
      // overflowed into next month, use last day of target month
      tentative = tentative.startOf('month').month(month).endOf('month')
    }

    selectedMonthDate.value = tentative.format('YYYY-MM-DD')
  }
}

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
    'reference_doctype',
    'reference_docname',
  ],
  filters: { status: 'Open', owner: user },
  pageLength: 9999,
  auto: true,
  transform: (data) => {
    return data.map((event) => {
      let fromDate = dayjs(event.starts_on).format('YYYY-MM-DD')
      let toDate = dayjs(event.ends_on).format('YYYY-MM-DD')
      let fromTime = dayjs(event.starts_on).format('HH:mm')
      let toTime = dayjs(event.ends_on).format('HH:mm')

      return {
        id: event.name,
        title: event.subject,
        description: event.description,
        status: event.status,
        fromDate,
        toDate,
        fromTime,
        toTime,
        isFullDay: event.all_day,
        eventType: event.event_type,
        color: event.color,
        referenceDoctype: event.reference_doctype,
        referenceDocname: event.reference_docname,
      }
    })
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
      starts_on: _event.fromDate + ' ' + _event.fromTime,
      ends_on: _event.toDate + ' ' + _event.toTime,
      all_day: _event.isFullDay || false,
      event_type: _event.eventType,
      color: _event.color,
      reference_doctype: _event.referenceDoctype,
      reference_docname: _event.referenceDocname,
      event_participants: _event.event_participants,
    },
    {
      onSuccess: async (e) => {
        await events.reload()
        showDetails({ id: e.name })
      },
    },
  )
}

async function updateEvent(_event) {
  if (!_event.id) return
  if (!mode.value || mode.value === 'edit' || mode.value === 'details') {
    // Ensure Contacts exist for participants referencing a new/unknown Contact, if not create them
    if (
      Array.isArray(_event.event_participants) &&
      _event.event_participants.length
    ) {
      _event.event_participants = await ensureParticipantContacts(
        _event.event_participants,
      )
    }

    events.setValue.submit(
      {
        name: _event.id,
        subject: _event.title,
        description: _event.description,
        starts_on: _event.fromDate + ' ' + _event.fromTime,
        ends_on: _event.toDate + ' ' + _event.toTime,
        all_day: _event.isFullDay,
        event_type: _event.eventType,
        color: _event.color,
        reference_doctype: _event.referenceDoctype,
        reference_docname: _event.referenceDocname,
        event_participants: _event.event_participants,
      },
      {
        onSuccess: async (e) => {
          await events.reload()
          showEventPanel.value && showDetails({ id: e.name })
        },
      },
    )
  }
}

function deleteEvent(eventID) {
  if (!eventID) return

  $dialog({
    title: __('Delete'),
    message: __('Are you sure you want to delete this event?'),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: (close) => {
          events.delete.submit(eventID, {
            onSuccess: () => events.reload(),
          })
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

function syncEvent(eventID, _event) {
  if (!eventID) return
  Object.assign(events.data.filter((event) => event.id === eventID)[0], _event)
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
  event.value = { id: _e.id }
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
  event.value = { id: _e.id }
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
  let toDate = e.toDate
  let isFullDay = e.isFullDay

  if (!duplicate) {
    let t = getFromToTime(e.time)
    fromTime = t[0]
    toTime = t[1]
    fromDate = dayjs(e.date).format('YYYY-MM-DD')
    toDate = fromDate
    e = { fromDate, toDate, fromTime, toTime, isFullDay }
  }

  event.value = {
    id: duplicate ? 'duplicate-event' : 'new-event',
    title: duplicate ? `${e.title} (Copy)` : '',
    description: e.description || '',
    date: fromDate,
    fromDate,
    toDate,
    fromTime,
    toTime,
    isFullDay: e.isFullDay || false,
    eventType: e.eventType || 'Public',
    color: e.color || 'green',
    referenceDoctype: e.referenceDoctype,
    referenceDocname: e.referenceDocname,
    event_participants: e.event_participants || [],
  }

  events.data.push(event.value)

  showEventPanel.value = true
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

async function ensureParticipantContacts(participants) {
  if (!Array.isArray(participants) || !participants.length) return participants
  const updated = []
  for (const part of participants) {
    const p = { ...part }
    try {
      if (
        p.reference_doctype === 'Contact' &&
        (!p.reference_docname || p.reference_docname === 'new') &&
        p.email
      ) {
        const firstName = p.email.split('@')[0] || p.email
        const contactDoc = await call('frappe.client.insert', {
          doc: {
            doctype: 'Contact',
            first_name: firstName,
            email_ids: [{ email_id: p.email, is_primary: 1 }],
          },
        })
        if (contactDoc?.name) p.reference_docname = contactDoc.name
      }
    } catch (e) {
      console.error('Failed creating contact for participant', p.email, e)
    }
    updated.push(p)
  }
  return updated
}
</script>
