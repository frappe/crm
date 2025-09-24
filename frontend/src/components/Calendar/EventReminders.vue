<template>
  <div>
    <div class="flex flex-col gap-2">
      <div
        class="flex gap-2"
        v-for="reminder in reminders"
        :key="reminder.name"
      >
        <FormControl
          class="w-28 shrink-0"
          type="select"
          :options="[
            {
              label: __('Notification'),
              value: 'Notification',
            },
            {
              label: __('Email'),
              value: 'Email',
            },
          ]"
          v-model="reminder.type"
          variant="outline"
          :placeholder="__('Select type')"
        />
        <FormControl
          class="w-fit"
          type="number"
          v-model.number="reminder.time"
          variant="outline"
          :placeholder="__('Enter time')"
        />
        <FormControl
          class="w-24 shrink-0"
          type="select"
          :options="[
            {
              label: __('minutes'),
              value: 'minutes',
            },
            {
              label: __('hours'),
              value: 'hours',
            },
            {
              label: __('days'),
              value: 'days',
            },
            {
              label: __('weeks'),
              value: 'weeks',
            },
          ]"
          v-model="reminder.unit"
          variant="outline"
          :placeholder="__('Select interval')"
        />
        <Button
          v-if="reminders.length > 1"
          icon="x"
          variant="outline"
          @click="reminders.splice(reminders.indexOf(reminder), 1)"
        />
      </div>
    </div>
    <Button
      class="mt-2"
      :label="__('Add Reminder')"
      :icon-left="BellIcon"
      @click="addReminder"
    />
  </div>
</template>
<script setup>
import BellIcon from '@/components/Icons/BellIcon.vue'
import { FormControl, Button } from 'frappe-ui'

const props = defineProps({
  size: {
    type: String,
    default: 'md',
  },
})

const reminders = defineModel()

function addReminder() {
  reminders.value.push({ type: 'Notification', time: 10, unit: 'minutes' })
}
</script>
