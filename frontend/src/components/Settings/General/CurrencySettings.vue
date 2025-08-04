<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8">
    <!-- Header -->
    <div class="flex px-2 justify-between">
      <div class="flex items-center gap-1 -ml-4 w-9/12">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Currency & Exchange rate provider')"
          size="md"
          @click="() => emit('updateStep', 'general-settings')"
          class="text-xl !h-7 font-semibold hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5"
        />
        <Badge
          v-if="settings.isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
      <div class="flex item-center space-x-2 w-3/12 justify-end">
        <Button
          :label="__('Update')"
          icon-left="plus"
          variant="solid"
          :disabled="!settings.isDirty"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <!-- Fields -->
    <div class="flex flex-1 flex-col overflow-y-auto">
      <div class="flex items-center justify-between gap-8 p-3">
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
          <div v-if="settings.doc?.currency" class="text-base text-ink-gray-8">
            {{ settings.doc.currency }}
          </div>
          <Link
            v-else
            class="form-control flex-1 truncate w-40"
            :value="settings.doc?.currency"
            doctype="Currency"
            @change="(v) => setCurrency(v)"
            :placeholder="__('Select currency')"
            placement="bottom-end"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex items-center justify-between gap-8 p-3">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Exchange rate provider') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('Configure the exchange rate provider for your CRM') }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            type="select"
            class="w-44"
            v-model="settings.doc.service_provider"
            :options="[
              { label: 'Frankfurter', value: 'frankfurter.app' },
              { label: 'Exchangerate Host', value: 'exchangerate.host' },
            ]"
            :placeholder="__('Select provider')"
            :disabled="!settings.doc?.currency"
          />
        </div>
      </div>
      <div
        v-if="settings.doc.service_provider === 'exchangerate.host'"
        class="h-px border-t mx-2 border-outline-gray-modals"
      />
      <div
        v-if="settings.doc.service_provider === 'exchangerate.host'"
        class="flex items-center justify-between gap-8 p-3"
      >
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Access key') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Access key for Exchangerate Host. Required for fetching exchange rates.',
              )
            }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('You can get your access key from ') }}
            <a
              class="hover:underline text-ink-gray-7"
              href="https://exchangerate.host/#/docs/access_key"
              target="_blank"
            >
              {{ __('exchangerate.host') }}
            </a>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            type="text"
            class="w-44"
            v-model="settings.doc.access_key"
            :placeholder="__('Enter access key')"
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
import { ErrorMessage } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { globalStore } from '@/stores/global'
import { showSettings } from '@/composables/settings'
import { ref } from 'vue'
import FormControl from 'frappe-ui/src/components/FormControl/FormControl.vue'

const { _settings: settings } = getSettings()
const { $dialog } = globalStore()

const emit = defineEmits(['updateStep'])
const errorMessage = ref('')

function updateSettings() {
  settings.save.submit(null, {
    validate: () => {
      errorMessage.value = ''
      if (!settings.doc?.currency) {
        errorMessage.value = __('Please select a currency before saving.')
        return errorMessage.value
      }
      if (
        settings.doc.service_provider === 'exchangerate.host' &&
        !settings.doc.access_key
      ) {
        errorMessage.value = __(
          'Please enter the Exchangerate Host access key.',
        )
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
