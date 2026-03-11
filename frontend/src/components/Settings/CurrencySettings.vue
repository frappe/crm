<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex justify-between px-2 text-ink-gray-8">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-xl font-semibold leading-none h-5">
          {{ __('Currency & Exchange Rate Provider') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __('Configure the Currency and Exchange Rate Provider for your CRM')
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
            {{ __('Currency') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Dashboard number cards & charts will show currency in the selected format. Once set, cannot be edited.',
              )
            }}
          </div>
        </div>
        <div>
          <div v-if="settings.doc?.currency" class="text-base text-ink-gray-8">
            {{ settings.doc.currency }}
          </div>
          <Link
            v-else
            class="form-control flex-1 truncate w-40"
            :value="settings.doc?.currency"
            doctype="Currency"
            :placeholder="__('Select Currency')"
            placement="bottom-end"
            @change="(v) => setCurrency(v)"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex items-center justify-between gap-8 py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Exchange Rate Provider') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Configure the Exchange Rate Provider for your CRM') }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            v-model="settings.doc.service_provider"
            type="select"
            class="w-44"
            :options="[
              { label: 'Frankfurter', value: 'frankfurter.app' },
              {
                label: 'Fawaz Ahmed Exchange API',
                value: 'fawazahmed-exchange-api',
              },
              { label: 'Exchangerate Host', value: 'exchangerate.host' },
              { label: 'Exchangerate API', value: 'exchangerate-api' },
            ]"
            :placeholder="__('Select Provider')"
            :disabled="!settings.doc?.currency"
            @update:modelValue="() => (settings.doc.access_key = '')"
          />
        </div>
      </div>
      <div
        v-if="requiresAccessKey"
        class="h-px border-t mx-2 border-outline-gray-modals"
      />
      <div
        v-if="requiresAccessKey"
        class="flex items-center justify-between gap-8 p-3"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Access Key') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __('Access Key for {0}. Required for fetching exchange rates.', [
                providerMeta.label,
              ])
            }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('You can get your Access Key from ') }}
            <a
              class="hover:underline text-ink-gray-7"
              :href="providerMeta.docsUrl"
              target="_blank"
            >
              {{ __(providerMeta.docsLabel) }}
            </a>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            v-model="settings.doc.access_key"
            type="text"
            class="w-44"
            :placeholder="__('Enter Access Key')"
            :disabled="!settings.doc?.currency"
          />
        </div>
      </div>
    </div>
    <div v-if="errorMessage" class="px-3">
      <ErrorMessage :message="__(errorMessage)" />
    </div>
  </div>
</template>
<script setup>
import { ErrorMessage, FormControl, toast } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { showSettings } from '@/composables/settings'
import { ref, computed } from 'vue'

const { _settings: settings } = getSettings()
const { $dialog } = globalStore()

const errorMessage = ref('')

const PROVIDERS_REQUIRING_KEY = ['exchangerate.host', 'exchangerate-api']

const PROVIDER_META = {
  'exchangerate.host': {
    label: 'Exchangerate Host',
    docsUrl: 'https://exchangerate.host/#/docs/access_key',
    docsLabel: 'exchangerate.host',
  },
  'exchangerate-api': {
    label: 'Exchangerate API',
    docsUrl: 'https://www.exchangerate-api.com',
    docsLabel: 'exchangerate-api.com',
  },
}

const serviceProvider = computed(() => settings.doc?.service_provider)
const requiresAccessKey = computed(() =>
  PROVIDERS_REQUIRING_KEY.includes(serviceProvider.value),
)
const providerMeta = computed(() => PROVIDER_META[serviceProvider.value])

function updateSettings() {
  settings.save.submit(null, {
    validate: () => {
      errorMessage.value = ''
      if (!settings.doc?.currency) {
        errorMessage.value = __('Please select a currency before saving.')
        return errorMessage.value
      }
      if (requiresAccessKey.value && !settings.doc.access_key) {
        errorMessage.value = __('Please enter the {0} Access Key.', [
          providerMeta.value.label,
        ])
        return errorMessage.value
      }
    },
    onSuccess: () => {
      showSettings.value = false
    },
  })
}

function setCurrency(value) {
  $dialog({
    title: __('Set Currency'),
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
