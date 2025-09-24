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
              'Configure your calendar settings like default view and reminder interval',
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
    <div class="flex flex-1 flex-col gap-4 overflow-y-auto">
      <div class="flex items-center justify-between gap-8 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Default Reminder') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Time before the event when a reminder will be sent by default. This will be applied to all events unless a custom reminder is set for a specific event',
              )
            }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            type="select"
            class="w-28"
            v-model="settings.doc.reminder_type"
            :options="[
              { label: __('Notification'), value: 'Notification' },
              { label: __('Email'), value: 'Email' },
            ]"
            :placeholder="__('Select reminder type')"
          />
          <FormControl
            type="number"
            class="w-[50px]"
            v-model="settings.doc.reminder_time"
            :placeholder="__('Enter time')"
          />
          <FormControl
            type="select"
            class="w-[90px]"
            v-model="settings.doc.reminder_unit"
            :options="[
              { label: __('minutes'), value: 'minutes' },
              { label: __('hours'), value: 'hours' },
              { label: __('days'), value: 'days' },
              { label: __('weeks'), value: 'weeks' },
            ]"
            :placeholder="__('Select interval')"
          />
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { FormControl } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'

const { _settings: settings } = getSettings()

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
    },
  })
}
</script>
