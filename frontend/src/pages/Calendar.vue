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
    </Calendar>
  </div>
</template>
<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Calendar, createListResource, TabButtons } from 'frappe-ui'

import { ref } from 'vue'

const _events = ref([
  {
    title: 'English by Ryan Mathew',
    participant: 'Ryan Mathew',
    id: 'EDU-CSH-2024-00091',
    venue: 'CNF-ROOM-2024-00001',
    fromDate: '2025-04-02 16:30:00',
    toDate: '2025-04-02 17:30:00',
    color: 'violet',
  },
  {
    title: 'English by Ryan Mathew',
    participant: 'Ryan Mathew',
    id: 'EDU-CSH-2024-00092',
    venue: 'CNF-ROOM-2024-00002',
    fromDate: '2025-04-04 13:30:00',
    toDate: '2025-04-04 17:30:00',
    color: 'green',
  },
  {
    title: 'English by Sheldon',
    participant: 'Sheldon',
    id: 'EDU-CSH-2024-00093',
    venue: 'CNF-ROOM-2024-00001',
    fromDate: '2025-04-16 10:30:00',
    toDate: '2025-04-16 11:30:00',
    color: 'blue',
  },
  {
    title: 'English by Ryan Mathew',
    participant: 'Ryan Mathew',
    id: 'EDU-CSH-2024-00094',
    venue: 'CNF-ROOM-2024-00001',
    fromDate: '2025-04-21 16:30:00',
    toDate: '2025-04-21 17:30:00',
    color: 'red',
  },
  {
    title: 'Google Meet with John ',
    participant: 'John',
    id: '#htrht41',
    venue: 'Google Meet',
    fromDate: '2025-04-11 00:00:00',
    toDate: '2025-04-11 23:59:59',
    color: 'amber',
    isFullDay: true,
  },
  {
    title: 'Zoom Meet with Sheldon',
    participant: 'Sheldon',
    id: '#htrht42',
    venue: 'Google Meet',
    fromDate: '2025-04-07 00:00:00',
    toDate: '2025-04-07 23:59:59',
    color: 'amber',
    isFullDay: true,
  },
])

const events = createListResource({
  doctype: 'Event',
  fields: ['name', 'status', 'subject', 'starts_on', 'ends_on'],
  filters: { status: 'Open' },
  auto: true,
  transform: (data) => {
    return data.map((event) => ({
      id: event.name,
      title: event.subject,
      fromDate: event.starts_on,
      toDate: event.ends_on,
      color: event.color,
    }))
  },
})

function createEvent(event) {
  events.insert.submit({
    subject: event.title,
    starts_on: event.fromDate,
    ends_on: event.toDate,
    color: event.color,
  })
}
function updateEvent(event) {
  events.setValue.submit({
    name: event.id,
    subject: event.title,
    starts_on: event.fromDate,
    ends_on: event.toDate,
    color: event.color,
  })
}
function deleteEvent(eventID) {
  events.delete.submit(eventID)
}
</script>
