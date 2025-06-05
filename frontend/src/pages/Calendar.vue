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
  <div class="flex h-screen px-5 flex-col overflow-hidden">
    <Calendar
      v-if="events.data?.length"
      :config="{
        defaultMode: 'Day',
        isEditMode: true,
        eventIcons: {
        },
        allowCustomClickEvents: true,
        redundantCellHeight: 100,
        enableShortcuts: false,
        noBorder: !true,
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
        <div class="my-4 flex justify-between">
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
import { sessionStore } from '@/stores/session'
import { Calendar, createListResource, TabButtons } from 'frappe-ui'
import {PhoneCallIcon} from "lucide-vue-next";

const { user } = sessionStore()

const events = createListResource({
  doctype: 'Event',
  fields: ['name', 'status', 'subject', 'starts_on', 'ends_on'],
  filters: { status: 'Open', owner: user },
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
  console.log(events);
  
  events.insert.submit({
    subject: event.title||"",
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