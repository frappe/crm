<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('General Settings') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Configure general settings for your application.') }}
      </p>
    </div>

    <div class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Update timestamp on new communication') }}
          </div>
          <div class="text-p-sm text-ink-gray-5 truncate">
            {{
              __(
                'Update the modified timestamp on new emails, messages & comments for leads & deals',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.update_timestamp_on_new_communication"
            size="sm"
            @update:modelValue="toggle('update_timestamp_on_new_communication')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Mark lead/deal as replied on response') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Automatically sets communication status to “Replied” for the lead or deal when a response is received. Applies only when SLA is enabled',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.auto_mark_replied_on_response"
            size="sm"
            @update:modelValue="toggle('auto_mark_replied_on_response')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Reopen lead/deal on new communication') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Automatically sets communication status to “Open” for the lead or deal when a new communication is created. Applies only when SLA is enabled',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.auto_reopen_on_new_communication"
            size="sm"
            @update:modelValue="toggle('auto_reopen_on_new_communication')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Morning digest email') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Email each sales user their follow-ups, replies, new assignments and tasks at about 8 AM their time. Users can opt out in their profile',
              )
            }}
          </div>
          <div
            v-if="settings.doc.enable_morning_digest && sender.data === false"
            class="mt-1 text-p-sm text-ink-amber-7"
          >
            {{
              __("No default outgoing email account. Digests won't be sent.")
            }}
            <button
              type="button"
              class="underline underline-offset-2 hover:text-ink-amber-8"
              @click="activeSettingsPage = 'Accounts'"
            >
              {{ __('Set one up') }}
            </button>
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.enable_morning_digest"
            size="sm"
            @update:modelValue="toggle('enable_morning_digest')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Timeline timestamp format') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Show timestamps in the activity timeline as relative time (5 mins ago) or an exact date & time',
              )
            }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="settings.doc.crm_timeline_timestamp_format"
            type="select"
            class="w-40"
            :options="timestampFormatOptions"
            :placeholder="__('Relative')"
            @update:modelValue="save()"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-gray-modals" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base font-medium text-ink-gray-7 truncate">
            {{ __('Timeline sort order') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Order of activities, emails, comments and calls in the timeline',
              )
            }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="settings.doc.crm_timeline_sort_order"
            type="select"
            class="w-40"
            :options="sortOrderOptions"
            :placeholder="__('Oldest First')"
            @update:modelValue="save()"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { activeSettingsPage } from '@/composables/settings'
import { getSettings } from '@/stores/settings'
import { FormControl, Switch, createResource, toast } from 'frappe-ui'

const { _settings: settings } = getSettings()

const sender = createResource({
  url: 'crm.api.digest.has_outgoing_email_account',
  auto: true,
})

const timestampFormatOptions = [
  { label: __('Relative'), value: 'Relative' },
  { label: __('Exact'), value: 'Exact' },
]
const sortOrderOptions = [
  { label: __('Oldest First'), value: 'Oldest First' },
  { label: __('Newest First'), value: 'Newest First' },
]

function toggle(settingKey) {
  settings.save.submit(null, {
    onSuccess: () => {
      toast.success(
        settings.doc[settingKey]
          ? __('Setting enabled successfully')
          : __('Setting disabled successfully'),
      )
    },
  })
}

function save() {
  settings.save.submit(null, {
    onSuccess: () => toast.success(__('Setting updated successfully')),
  })
}
</script>
