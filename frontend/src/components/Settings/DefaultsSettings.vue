<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex justify-between px-2 text-ink-gray-8">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
          {{ __('System Defaults') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Configure default settings for your CRM system, including default currency, date formats, and other system-wide preferences to ensure consistency across your system.',
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

    <div class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex items-center justify-between gap-4 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
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
            doctype="Currency"
            class="w-24"
          />
        </div>
      </div>
      <div class="flex items-center justify-between gap-4 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Currency Precision') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Number of decimal places used for all currency values') }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.currency_precision"
            :options="getOptions('currency_precision')"
            :placeholder="3"
            class="!w-16"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex items-center justify-between gap-4 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
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
            :options="getOptions('number_format')"
            class="!w-32"
          />
        </div>
      </div>
      <div class="flex items-center justify-between gap-4 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Float Precision') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Number of decimal places for non-currency numeric fields') }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.float_precision"
            :options="getOptions('float_precision')"
            :placeholder="3"
            class="!w-16"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex items-center justify-between gap-4 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Date Format') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Display format for dates across the system') }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.date_format"
            :options="getOptions('date_format')"
            class="!w-32"
          />
        </div>
      </div>
      <div class="flex items-center justify-between gap-4 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Time Format') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Select whether to display time with or without seconds') }}
          </div>
        </div>
        <div>
          <Select
            v-model="settings.doc.time_format"
            :options="getOptions('time_format')"
            class="!w-28"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { getMeta } from '@/stores/meta'
import { Select, Button, toast, createDocumentResource } from 'frappe-ui'
import { computed } from 'vue'

const { getFields } = getMeta('System Settings')

const settings = createDocumentResource({
  doctype: 'System Settings',
  name: 'System Settings',
})

const isDirty = computed(() => {
  return JSON.stringify(settings.doc) !== JSON.stringify(settings.originalDoc)
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
