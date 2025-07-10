<template>
  <div class="flex h-full flex-col gap-6 p-8 text-ink-gray-8">
    <div class="flex flex-col gap-1">
      <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
        {{ __('General') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Configure general settings for your CRM') }}
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
                'Makes "Close Date" and "Deal Value" mandatory for deal value forecasting',
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
        class="flex items-center justify-between gap-8 p-3 cursor-pointer hover:bg-surface-menu-bar rounded"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Currency') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'CRM currency for all monetary values. Once set, cannot be edited.',
              )
            }}
          </div>
        </div>
        <div>
          <div v-if="settings.doc.currency" class="text-base text-ink-gray-8">
            {{ settings.doc.currency }}
          </div>
          <Link
            v-else
            class="form-control flex-1 truncate w-40"
            :value="settings.doc.currency"
            doctype="Currency"
            @change="(v) => setCurrency(v)"
            :placeholder="__('Select currency')"
            placement="bottom-end"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <template v-for="(setting, i) in settingsList" :key="setting.name">
        <li
          class="flex items-center justify-between p-3 cursor-pointer hover:bg-surface-menu-bar rounded"
          @click="() => emit('updateStep', setting.name)"
        >
          <div class="flex flex-col">
            <div class="text-p-base font-medium text-ink-gray-7 truncate">
              {{ __(setting.label) }}
            </div>
            <div class="text-p-sm text-ink-gray-5 truncate">
              {{ __(setting.description) }}
            </div>
          </div>
          <div>
            <FeatherIcon name="chevron-right" class="text-ink-gray-7 size-4" />
          </div>
        </li>
        <div
          v-if="settingsList.length !== i + 1"
          class="h-px border-t mx-2 border-outline-gray-modals"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { Switch, toast } from 'frappe-ui'

const emit = defineEmits(['updateStep'])

const { _settings: settings } = getSettings()
const { $dialog } = globalStore()

const settingsList = [
  {
    name: 'brand-settings',
    label: 'Brand settings',
    description: 'Configure your brand name, logo and favicon',
  },
  {
    name: 'home-actions',
    label: 'Home actions',
    description: 'Configure actions that appear on the home dropdown',
  },
]

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

function setCurrency(value) {
  $dialog({
    title: __('Set currency'),
    message: __(
      'Are you sure you want to set the currency as {0}? This cannot be changed later.',
      [value],
    ),
    variant: 'solid',
    theme: 'blue',
    actions: [
      {
        label: __('Save'),
        variant: 'solid',
        onClick: (close) => {
          settings.doc.currency = value
          settings.save.submit(null, {
            onSuccess: () => {
              toast.success(__('Currency set as {0} successfully', [value]))
              close()
            },
          })
        },
      },
    ],
  })
}
</script>
