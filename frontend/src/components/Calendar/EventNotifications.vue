<template>
  <div class="flex flex-col gap-2">
    <div v-if="notifications?.length" class="flex flex-col gap-2">
      <div v-for="(notification, i) in notifications" :key="notification.name">
        <div v-if="isAllDay" class="flex flex-col items-center gap-2">
          <div class="flex items-center gap-2 w-full">
            <FormControl
              class="flex-1 shrink-0"
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
              v-model="notification.type"
              variant="outline"
              :placeholder="__('Select type')"
            />
            <Button
              icon="x"
              variant="outline"
              @click="
                notifications.splice(notifications.indexOf(notification), 1)
              "
            />
          </div>
          <div class="flex items-center gap-2">
            <FormControl
              class="w-fit"
              type="number"
              :min="min(notification)"
              :max="max(notification)"
              @blur="handleIntervalChange(notification)"
              v-model.number="notification.before"
              variant="outline"
              :placeholder="__('10')"
            />
            <FormControl
              class="w-20 shrink-0"
              type="select"
              :options="intervalOptions(notification)"
              v-model="notification.interval"
              @change="() => handleIntervalChange(notification)"
              variant="outline"
              :placeholder="__('minutes')"
            />
            <div v-if="isAllDay" class="text-p-sm text-ink-gray-5 shrink-0">
              {{ __('before at') }}
            </div>
            <TimePicker
              v-if="isAllDay"
              class="w-24 shrink-0"
              v-model="notification.time"
              variant="outline"
              :placeholder="__('08:00 AM')"
            />
          </div>
          <div
            v-if="i < notifications.length - 1"
            class="w-full border-t border-outline-gray-1"
          />
        </div>
        <div v-else class="flex items-center gap-2">
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
            v-model="notification.type"
            variant="outline"
            :placeholder="__('Select type')"
          />
          <FormControl
            class="w-fit"
            type="number"
            :min="min(notification)"
            :max="max(notification)"
            :step="notification.interval === 'minutes' ? 5 : 1"
            @blur="handleIntervalChange(notification)"
            v-model.number="notification.before"
            variant="outline"
            :placeholder="__('10')"
          />
          <FormControl
            class="w-24 shrink-0"
            type="select"
            :options="intervalOptions(notification)"
            v-model="notification.interval"
            @change="() => handleIntervalChange(notification)"
            variant="outline"
            :placeholder="__('minutes')"
          />
          <Button
            icon="x"
            variant="outline"
            @click="
              notifications.splice(notifications.indexOf(notification), 1)
            "
          />
        </div>
      </div>
    </div>
    <Button
      variant="outline"
      :label="__('Add notification')"
      :icon-left="BellIcon"
      @click="addNotification"
    />
  </div>
</template>
<script setup>
import BellIcon from '@/components/Icons/BellIcon.vue'
import { min, max, handleIntervalChange } from '@/components/Calendar/utils'
import { TimePicker } from 'frappe-ui'

const props = defineProps({
  isAllDay: {
    type: Boolean,
    default: false,
  },
})

const notifications = defineModel()

const intervalOptions = (n) => {
  if (props.isAllDay) {
    if (n.interval === 'minutes' || n.interval === 'hours') {
      n.interval = 'days'
    }

    if (!n.time) {
      n.time = '08:00'
    }

    return [
      { label: n.before == 1 ? __('day') : __('days'), value: 'days' },
      { label: n.before == 1 ? __('week') : __('weeks'), value: 'weeks' },
    ]
  }
  return [
    { label: n.before == 1 ? __('minute') : __('minutes'), value: 'minutes' },
    { label: n.before == 1 ? __('hour') : __('hours'), value: 'hours' },
    { label: n.before == 1 ? __('day') : __('days'), value: 'days' },
    { label: n.before == 1 ? __('week') : __('weeks'), value: 'weeks' },
  ]
}

function addNotification() {
  notifications.value ??= []
  if (props.isAllDay) {
    notifications.value.push({
      type: 'Notification',
      before: 1,
      interval: 'days',
      time: '08:00',
    })
  } else {
    notifications.value.push({
      type: 'Notification',
      before: 10,
      interval: 'minutes',
    })
  }
}
</script>
