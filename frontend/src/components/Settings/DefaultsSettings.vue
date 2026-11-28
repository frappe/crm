<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-sm:px-2 max-sm:py-4"
  >
    <div class="flex justify-between px-2 text-ink-gray-8 max-sm:hidden">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('System Defaults') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Set the currency, number, date and time formats used across your CRM.',
            )
          }}
        </p>
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          v-if="isDirty"
          :label="__('Update')"
          variant="solid"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <div v-if="settings.doc" class="flex-1 flex flex-col overflow-y-auto">
      <div
        class="flex items-center justify-between gap-4 py-3 px-2 max-sm:flex-col max-sm:items-stretch max-sm:gap-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('Currency') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Defines the default currency for all records, can be overridden at the field level',
              )
            }}
          </div>
        </div>
        <div>
          <Link
            v-model="settings.doc.currency"
            :sheet-title="__('Currency')"
            doctype="Currency"
            class="w-24 max-sm:w-full"
          />
        </div>
      </div>
      <div
        class="flex items-center justify-between gap-4 py-3 px-2 max-sm:flex-col max-sm:items-stretch max-sm:gap-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('Currency Precision') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Number of decimal places used for all currency values') }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.currency_precision"
            :sheet-title="__('Currency Precision')"
            :options="getOptions('currency_precision')"
            placeholder="3"
            class="!w-16 max-sm:!w-full"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div
        class="flex items-center justify-between gap-4 py-3 px-2 max-sm:flex-col max-sm:items-stretch max-sm:gap-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('Number Format') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Controls how numbers are displayed (e.g., commas, decimal separators)',
              )
            }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.number_format"
            :sheet-title="__('Number Format')"
            :options="getOptions('number_format')"
            class="!w-32 max-sm:!w-full"
          />
        </div>
      </div>
      <div
        class="flex items-center justify-between gap-4 py-3 px-2 max-sm:flex-col max-sm:items-stretch max-sm:gap-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('Float Precision') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Number of decimal places for non-currency numeric fields') }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.float_precision"
            :sheet-title="__('Float Precision')"
            :options="getOptions('float_precision')"
            placeholder="3"
            class="!w-16 max-sm:!w-full"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div
        class="flex items-center justify-between gap-4 py-3 px-2 max-sm:flex-col max-sm:items-stretch max-sm:gap-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('Date Format') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Display format for dates across the system') }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.date_format"
            :sheet-title="__('Date Format')"
            :options="getOptions('date_format')"
            class="!w-32 max-sm:!w-full"
          />
        </div>
      </div>
      <div
        class="flex items-center justify-between gap-4 py-3 px-2 max-sm:flex-col max-sm:items-stretch max-sm:gap-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 sm:truncate">
            {{ __('Time Format') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Select whether to display time with or without seconds') }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.time_format"
            :sheet-title="__('Time Format')"
            :options="getOptions('time_format')"
            class="!w-28 max-sm:!w-full"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import Select from '@/components/Controls/Select.vue'
import { useSettingsSaveBar } from '@/components/Settings/settingsPhone'
import { getMeta } from '@/stores/meta'
import { Button, toast, createDocumentResource } from 'frappe-ui'
import { computed } from 'vue'

const { getFields } = getMeta('System Settings')

const settings = createDocumentResource({
  doctype: 'System Settings',
  name: 'System Settings',
})

const isDirty = computed(() => {
  return JSON.stringify(settings.doc) !== JSON.stringify(settings.originalDoc)
})

useSettingsSaveBar({
  isDirty: () => isDirty.value,
  saving: () => settings.save.loading,
  save: updateSettings,
  discard: () =>
    (settings.doc = JSON.parse(JSON.stringify(settings.originalDoc))),
})

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Settings updated successfully'))
    },
    onError(error) {
      const message = error?.messages?.[0] || __('Failed to save settings')
      toast.error(message)
    },
  })
}

const fieldsMeta = computed(() => getFields() || [])

function getOptions(fieldname) {
  const field = fieldsMeta.value.find((f) => f.fieldname === fieldname)
  return field?.options || []
}
</script>
