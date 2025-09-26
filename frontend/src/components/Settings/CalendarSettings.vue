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
    </div>
  </div>
</template>
<script setup>
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'
import { FormControl } from 'frappe-ui'

const { _settings: settings } = getSettings()

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
    },
  })
}
</script>
