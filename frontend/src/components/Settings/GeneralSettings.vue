<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('General Settings') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{ __('Configure general settings for your application') }}
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
                'Update the modified timestamp on new email communication & comments for leads & deals',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            :model-value="
              Boolean(settings.doc.update_timestamp_on_new_communication)
            "
            size="sm"
            @update:model-value="
              (value) => toggle('update_timestamp_on_new_communication', value)
            "
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
            :model-value="Boolean(settings.doc.auto_mark_replied_on_response)"
            size="sm"
            @update:model-value="
              (value) => toggle('auto_mark_replied_on_response', value)
            "
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
            :model-value="
              Boolean(settings.doc.auto_reopen_on_new_communication)
            "
            size="sm"
            @update:model-value="
              (value) => toggle('auto_reopen_on_new_communication', value)
            "
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Follow up reminders') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Notify the users assigned to a lead or deal when its next follow up is due',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            :model-value="Boolean(settings.doc.enable_follow_up_reminders)"
            size="sm"
            @update:model-value="
              (value) => toggle('enable_follow_up_reminders', value)
            "
          />
        </div>
      </div>
      <div
        v-if="settings.doc.enable_follow_up_reminders"
        class="flex gap-4 items-center justify-between py-3 px-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Remind before') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{ __('How far ahead of the follow up time the reminder is sent') }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            v-model.number="settings.doc.follow_up_reminder_before"
            type="number"
            min="0"
            class="w-20"
            :placeholder="__('30')"
            @change="save()"
          />
          <FormControl
            v-model="settings.doc.follow_up_reminder_interval"
            type="select"
            class="w-28"
            :options="reminderIntervalOptions"
            :placeholder="__('minutes')"
            @update:modelValue="save()"
          />
        </div>
      </div>
      <div
        v-if="settings.doc.enable_follow_up_reminders"
        class="flex gap-4 items-center justify-between py-3 px-2"
      >
        <div class="flex flex-col">
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Email follow up reminders') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Also email the reminder, in addition to the in-app notification',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            :model-value="Boolean(settings.doc.send_follow_up_reminder_email)"
            size="sm"
            @update:model-value="
              (value) => toggle('send_follow_up_reminder_email', value)
            "
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
import { getSettings } from '@/stores/settings'
import { FormControl, Switch, toast } from 'frappe-ui'

const { _settings: settings } = getSettings()

const timestampFormatOptions = [
  { label: __('Relative'), value: 'Relative' },
  { label: __('Exact'), value: 'Exact' },
]
const sortOrderOptions = [
  { label: __('Oldest First'), value: 'Oldest First' },
  { label: __('Newest First'), value: 'Newest First' },
]
const reminderIntervalOptions = [
  { label: __('minutes'), value: 'minutes' },
  { label: __('hours'), value: 'hours' },
  { label: __('days'), value: 'days' },
]

function toggle(settingKey, value) {
  // Frappe Check fields are 0/1, but Switch is backed by a control that only
  // recognises real booleans. Binding the raw 0/1 leaves the two out of sync:
  // the switch paints itself "on" from the truthy value while its own state
  // stays unchecked, so every click emits `true` and the setting can be turned
  // on but never off. Hence Boolean() in, 0/1 back out.
  settings.doc[settingKey] = value ? 1 : 0
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
