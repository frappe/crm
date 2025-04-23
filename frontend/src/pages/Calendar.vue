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
  </div>
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { sessionStore } from '@/stores/session'
import { globalStore } from '@/stores/global'
import { Calendar, createListResource, TabButtons } from 'frappe-ui'

const { user } = sessionStore()
const { $dialog } = globalStore()

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
</script>
