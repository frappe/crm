<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <div class="flex flex-col gap-1">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('Forecasting') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Configure forecasting settings for your CRM') }}
      </p>
    </div>

    <div class="flex-1 flex flex-col overflow-y-auto">
      <div
        class="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-menu-bar rounded"
        @click="toggleForecasting()"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Enable forecasting') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __(
                'Makes "Expected Closure Date" and "Expected Deal Value" mandatory for deal value forecasting',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            size="sm"
            v-model="settings.doc.enable_forecasting"
            @click.stop="toggleForecasting(settings.doc.enable_forecasting)"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div
        class="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-menu-bar rounded"
        @click="autoUpdateExpectedDealValue"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Auto update expected deal value') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __(
                'Automatically update "Expected Deal Value" based on the total value of associated products in a deal',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            size="sm"
            v-model="settings.doc.auto_update_expected_deal_value"
            @click.stop="autoUpdateExpectedDealValue"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getSettings } from '@/stores/settings'
import { Switch, toast } from 'frappe-ui'

const { _settings: settings } = getSettings()

function toggleForecasting(value) {
  settings.doc.enable_forecasting =
    value !== undefined ? value : !settings.doc.enable_forecasting

  settings.save.submit(null, {
    onSuccess: () => {
      toast.success(
        settings.doc.enable_forecasting
          ? __('Forecasting enabled successfully')
          : __('Forecasting disabled successfully'),
      )
    },
  })
}

function autoUpdateExpectedDealValue() {
  settings.doc.auto_update_expected_deal_value =
    !settings.doc.auto_update_expected_deal_value

  settings.save.submit(null, {
    onSuccess: () => {
      toast.success(
        settings.doc.auto_update_expected_deal_value
          ? __('Auto update of expected deal value enabled')
          : __('Auto update of expected deal value disabled'),
      )
    },
  })
}
</script>
