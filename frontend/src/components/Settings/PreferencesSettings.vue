<template>
  <SettingsLayoutBase
    v-if="user.doc"
    :title="__('Preferences')"
    :description="
      __(
        'Choose how you want to use the application by setting your preferences.',
      )
    "
  >
    <template #content>
      <div>
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center">
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __('Appearance') }}
            </div>
          </div>
        </div>
        <div class="flex flex-col gap-4 my-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Theme') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Switch between light, dark, or system theme') }}
            </span>
          </div>
          <ThemeSwitcher
            :logo="brand.logo || CRMLogo"
            :name="brand.name || 'CRM'"
          />
        </div>
        <div class="flex items-center justify-between">
          <div class="flex gap-2 items-center h-7">
            <div class="text-base font-semibold text-ink-gray-9">
              {{ __('Language & Time') }}
            </div>
            <Badge
              v-if="isDirty"
              :variant="'subtle'"
              :theme="'orange'"
              size="sm"
              :label="__('Not Saved')"
            />
          </div>
          <Button
            v-if="isDirty"
            :label="__('Save')"
            :loading="user.save.loading"
            @click="save()"
          />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Language') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Change language of the application.') }}
            </span>
          </div>
          <Link v-model="user.doc.language" doctype="Language" class="w-40" />
        </div>
        <div class="flex items-center justify-between mt-6">
          <div class="flex flex-col gap-1">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Timezone') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{ __('Change timezone of the application.') }}
            </span>
          </div>
          <Combobox
            v-model="user.doc.time_zone"
            class="w-40"
            :options="getTimezoneOptions()"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import ThemeSwitcher from '@/components/Settings/ThemeSwitcher.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import Link from '@/components/Controls/Link.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { getSettings } from '@/stores/settings'
import {
  Combobox,
  Badge,
  toast,
  createResource,
  createDocumentResource,
} from 'frappe-ui'
import { ref, computed, inject } from 'vue'

const refreshRequired = ref(false)

const { user: sessionUser } = inject('session')

const { brand } = getSettings()
const user = createDocumentResource({ doctype: 'User', name: sessionUser })

function save() {
  refreshRequired.value =
    user.doc.language !== user.originalDoc?.language ||
    user.doc.time_zone !== user.originalDoc?.time_zone

  user.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Preferences Updated Successfully'))
      if (refreshRequired.value) {
        window.location.reload()
      }
    },
    onError: (err) => {
      toast.error(err.message + ': ' + err.messages[0])
    },
  })
}

const isDirty = computed(() => {
  return JSON.stringify(user.doc) !== JSON.stringify(user.originalDoc)
})

const timeZones = createResource({
  url: 'frappe.core.doctype.user.user.get_timezones',
  cache: 'TimeZones',
  auto: true,
})

function getTimezoneOptions() {
  return timeZones.data?.timezones.map((tz) => ({ label: tz, value: tz })) || []
}

useKeyboardShortcuts({
  ignoreTyping: false,
  shortcuts: [
    {
      match: (e) => (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's',
      action: () => {
        if (isDirty.value) {
          save()
        }
      },
    },
  ],
})
</script>
