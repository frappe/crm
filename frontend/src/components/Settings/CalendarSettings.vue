<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between px-2 text-ink-gray-8">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
          {{ __('Calendar settings') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Configure your calendar settings like default view and event notifications here',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Update')"
          variant="solid"
          :disabled="!settings.isDirty"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <!-- Fields -->
    <div class="flex flex-1 flex-col overflow-y-auto">
      <div class="flex items-center justify-between gap-8 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Default view') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Select the default view for your calendar. This will be the initial view when you open the calendar',
              )
            }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            type="select"
            class="w-28"
            :options="[
              { label: __('Daily'), value: 'Daily' },
              { label: __('Weekly'), value: 'Weekly' },
              { label: __('Monthly'), value: 'Monthly' },
            ]"
            v-model="settings.doc.default_calendar_view"
            :placeholder="__('Select view')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex flex-col gap-3 px-2 py-3">
        <div>
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Event notifications') }}
          </div>
          <div
            class="text-p-sm text-ink-gray-5"
            v-html="
              __(
                'Reminders will be sent <b>before the event starts</b>, based on the configured time',
              )
            "
          />
        </div>
        <div
          v-if="notifications?.length"
          class="rounded-lg flex flex-col gap-2 w-fit"
        >
          <div v-for="notification in notifications" :key="notification.name">
            <div class="flex items-center gap-2">
              <FormControl
                class="w-36 shrink-0"
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
                :placeholder="__('Notification')"
              />
              <FormControl
                class="w-20 shrink-0"
                type="number"
                :min="min(notification)"
                :max="max(notification)"
                :step="notification.interval == 'minutes' ? 5 : 1"
                @blur="handleIntervalChange(notification)"
                v-model.number="notification.before"
                :placeholder="__('10')"
              />
              <FormControl
                class="w-32 shrink-0"
                type="select"
                :options="[
                  {
                    label:
                      notification.before == 1 ? __('minute') : __('minutes'),
                    value: 'minutes',
                  },
                  {
                    label: notification.before == 1 ? __('hour') : __('hours'),
                    value: 'hours',
                  },
                  {
                    label: notification.before == 1 ? __('day') : __('days'),
                    value: 'days',
                  },
                  {
                    label: notification.before == 1 ? __('week') : __('weeks'),
                    value: 'weeks',
                  },
                ]"
                v-model="notification.interval"
                @change="() => handleIntervalChange(notification)"
                :placeholder="__('minutes')"
              />
              <Button
                icon="x"
                variant="ghost"
                @click="
                  notifications.splice(notifications.indexOf(notification), 1)
                "
              />
            </div>
          </div>
        </div>
        <Button
          class="w-fit"
          :label="__('Add notification')"
          iconLeft="plus"
          @click="
            notifications.push({
              type: 'Notification',
              before: 10,
              interval: 'minutes',
            })
          "
        />
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex flex-col gap-3 py-3 px-2">
        <div>
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('All day event notifications') }}
          </div>
          <div
            class="text-p-sm text-ink-gray-5"
            v-html="
              __(
                'For all-day events, <b>set a time</b> to send reminders before the event starts',
              )
            "
          />
        </div>
        <div
          v-if="allDayNotifications?.length"
          class="rounded-lg flex flex-col gap-2 w-fit"
        >
          <div
            v-for="notification in allDayNotifications"
            :key="notification.name"
          >
            <div class="flex items-center gap-2">
              <FormControl
                class="w-36 shrink-0"
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
                :placeholder="__('Notification')"
              />
              <FormControl
                class="w-20 shrink-0"
                type="number"
                :min="min(notification)"
                :max="max(notification)"
                @blur="handleIntervalChange(notification)"
                v-model.number="notification.before"
                :placeholder="__('10')"
              />
              <FormControl
                class="w-32 shrink-0"
                type="select"
                :options="[
                  {
                    label: notification.before == 1 ? __('day') : __('days'),
                    value: 'days',
                  },
                  {
                    label: notification.before == 1 ? __('week') : __('weeks'),
                    value: 'weeks',
                  },
                ]"
                v-model="notification.interval"
                @change="() => handleIntervalChange(notification)"
                :placeholder="__('minutes')"
              />
              <div class="text-p-sm text-ink-gray-5">
                {{ __('before at') }}
              </div>
              <TimePicker
                class="w-32 shrink-0"
                v-model="notification.time"
                :placeholder="__('08:00 pm')"
              />
              <Button
                icon="x"
                variant="ghost"
                @click="
                  allDayNotifications.splice(
                    allDayNotifications.indexOf(notification),
                    1,
                  )
                "
              />
            </div>
          </div>
        </div>
        <Button
          class="w-fit"
          :label="__('Add notification')"
          iconLeft="plus"
          @click="
            allDayNotifications.push({
              type: 'Notification',
              before: 1,
              interval: 'days',
              time: '08:00',
            })
          "
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'
import { min, max, handleIntervalChange } from '@/components/Calendar/utils'
import { FormControl, TimePicker } from 'frappe-ui'
import { computed } from 'vue'

const { _settings: settings } = getSettings()

const notifications = computed({
  get: () => settings.doc.event_notifications || [],
  set: (val) => (settings.doc.event_notifications = val),
})

const allDayNotifications = computed({
  get: () => settings.doc.all_day_event_notifications || [],
  set: (val) => (settings.doc.all_day_event_notifications = val),
})

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
    },
  })
}
</script>
