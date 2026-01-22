<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('Forecasting') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Configure forecasting feature to help predict sales performance and growth',
          )
        }}
      </p>
    </div>

    <div class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Enable forecasting') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __(
                'Makes "Expected closure date" and "Expected deal value" mandatory for deal value forecasting',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            size="sm"
            v-model="settings.doc.enable_forecasting"
            @click.stop="toggleForecasting"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Auto update expected deal value') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __(
                'Automatically update "Expected deal value" based on the total value of associated products in a deal',
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

function toggleForecasting() {
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
