<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8 max-sm:px-2 max-sm:py-4"
  >
    <!-- Header -->
    <div class="flex justify-between px-2 text-ink-gray-8 max-sm:hidden">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Calendar Settings') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Configure your calendar settings, including the default view and event notifications',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          v-if="settings.isDirty"
          :label="__('Update')"
          variant="solid"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <!-- Fields -->
    <div class="flex flex-1 flex-col overflow-y-auto">
      <div
        class="flex items-center justify-between gap-8 py-3 px-2 max-sm:flex-col max-sm:items-stretch max-sm:gap-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('Default View') }}
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
          <Select
            v-model="settings.doc.default_calendar_view"
            class="w-28 max-sm:w-full"
            :options="[
              { label: __('Daily'), value: 'Daily' },
              { label: __('Weekly'), value: 'Weekly' },
              { label: __('Monthly'), value: 'Monthly' },
            ]"
            :placeholder="__('Select View')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex flex-col gap-3 px-2 py-3">
        <div>
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('Event Notifications') }}
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
          class="rounded-6 flex flex-col gap-2 w-fit max-sm:w-full"
        >
          <div v-for="notification in notifications" :key="notification.name">
            <div
              class="flex items-center gap-2 max-sm:grid max-sm:grid-cols-[minmax(0,1fr)_4rem_minmax(0,1fr)_auto]"
            >
              <Select
                v-model="notification.type"
                class="w-36 shrink-0 max-sm:w-full"
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
                :placeholder="__('Notification')"
              />
              <FormControl
                v-model.number="notification.before"
                class="w-20 shrink-0 max-sm:w-full"
                type="number"
                :min="min(notification)"
                :max="max(notification)"
                :step="notification.interval == 'minutes' ? 5 : 1"
                :placeholder="__('10')"
                @blur="handleIntervalChange(notification)"
              />
              <Select
                v-model="notification.interval"
                class="w-32 shrink-0 max-sm:w-full"
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
                :placeholder="__('minutes')"
                @update:modelValue="() => handleIntervalChange(notification)"
              />
              <Button
                icon="lucide-x"
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
          :label="__('Add Notification')"
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
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex flex-col gap-3 py-3 px-2">
        <div>
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('All Day Event Notifications') }}
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
          class="rounded-6 flex flex-col gap-2 w-fit max-sm:w-full"
        >
          <div
            v-for="notification in allDayNotifications"
            :key="notification.name"
          >
            <div
              class="flex items-center gap-2 max-sm:grid max-sm:grid-cols-[minmax(0,1fr)_4rem_minmax(0,1fr)_auto]"
            >
              <Select
                v-model="notification.type"
                class="w-36 shrink-0 max-sm:w-full"
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
                :placeholder="__('Notification')"
              />
              <FormControl
                v-model.number="notification.before"
                class="w-20 shrink-0 max-sm:w-full"
                type="number"
                :min="min(notification)"
                :max="max(notification)"
                :placeholder="__('10')"
                @blur="handleIntervalChange(notification)"
              />
              <Select
                v-model="notification.interval"
                class="w-32 shrink-0 max-sm:w-full"
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
                :placeholder="__('minutes')"
                @update:modelValue="() => handleIntervalChange(notification)"
              />
              <div class="text-p-sm text-ink-gray-5">
                {{ __('before at') }}
              </div>
              <TimePicker
                v-model="notification.time"
                class="w-32 shrink-0 max-sm:col-span-2 max-sm:w-full"
                :placeholder="__('08:00 pm')"
              />
              <Button
                class="max-sm:col-start-4 max-sm:row-start-1"
                icon="lucide-x"
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
          :label="__('Add Notification')"
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
import Select from '@/components/Controls/Select.vue'
import { useSettingsSaveBar } from '@/components/Settings/settingsPhone'
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

useSettingsSaveBar({
  isDirty: () => settings.isDirty,
  saving: () => settings.save.loading,
  save: updateSettings,
  discard: () =>
    (settings.doc = JSON.parse(JSON.stringify(settings.originalDoc))),
})

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
    },
  })
}
</script>
