<template>
  <SettingsLayoutBase v-if="user.doc">
    <template #title>
      <div class="flex gap-1 items-center max-sm:hidden">
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="__('Email Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 text-2xl-semibold hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'profile-settings')"
        />
        <Badge
          v-if="isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="amber"
        />
      </div>
    </template>
    <template #header-actions>
      <Button
        v-if="isDirty && !isPhone"
        variant="solid"
        :label="__('Update')"
        @click="update"
      />
    </template>
    <template #content>
      <EmailSubjectSettings
        :key="discards"
        :doc="user.doc"
        @change="(field, val) => (user.doc[field] = val)"
      />
      <div class="flex flex-col gap-4 mt-16 max-sm:mt-10">
        <div class="flex flex-col gap-1">
          <span class="text-base-medium text-ink-gray-8">
            {{ __('Signature') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{ __('Manage your email signature') }}
          </span>
        </div>
        <RichTextField
          editor-class="prose-sm min-h-28 max-w-full border rounded-b-6 border-t-0 p-2 border-outline-elevation-2"
          :content="user.doc.email_signature"
          placeholder="Type something..."
          :fixed-menu="true"
          @change="(val) => (user.doc.email_signature = val)"
        />
      </div>
      <div class="flex flex-col gap-4 mt-16 max-sm:mt-10">
        <div class="flex flex-col gap-1">
          <span class="text-base-medium text-ink-gray-8">
            {{ __('Emails') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __('Switch between outgoing email accounts when sending emails')
            }}
          </span>
        </div>
        <div>
          <div
            v-if="user.doc.user_emails?.length"
            class="w-full border rounded-5 mb-2 border-outline-elevation-2"
          >
            <div
              class="grid grid-cols-[4fr_4fr_0.3fr] gap-2 px-4 py-3 text-sm-medium text-ink-gray-5 border-b border-outline-elevation-2 max-sm:hidden"
            >
              <span>{{ __('Email Account') }}</span>
              <span>{{ __('Email') }}</span>
              <span></span>
            </div>
            <div
              v-for="e in user.doc.user_emails"
              :key="e.name"
              class="grid grid-cols-[4fr_4fr_0.3fr] gap-2 group items-center px-4 py-2.5 text-base border-b border-outline-elevation-2 last:border-b-0 max-sm:min-h-14 max-sm:grid-cols-[minmax(0,1fr)_auto] max-sm:gap-x-2 max-sm:gap-y-0.5"
            >
              <span
                class="text-ink-gray-8 font-medium truncate max-sm:text-ink-gray-9"
              >
                {{ e.email_account }}
              </span>
              <span
                class="text-ink-gray-6 truncate max-sm:col-start-1 max-sm:text-sm max-sm:text-ink-gray-5"
              >
                {{ e.email_id }}
              </span>
              <div
                class="group-hover:opacity-100 opacity-0 transition-opacity max-sm:col-start-2 max-sm:row-span-2 max-sm:row-start-1 max-sm:opacity-100"
              >
                <Button
                  class="w-10"
                  variant="ghost"
                  :tooltip="__('Remove')"
                  icon="lucide-x"
                  @click.prevent="removeEmail(e)"
                />
              </div>
            </div>
          </div>
          <Combobox
            :model-value="null"
            :options="filteredEmails"
            @update:selected-option="(e) => addEmail(e)"
          >
            <template #trigger="{ open, setOpen }">
              <Button
                class="!bg-surface-elevation-2"
                variant="outline"
                :label="__('Add Email')"
                iconLeft="lucide-plus"
                @click="setOpen(!open)"
              />
            </template>
            <template #item-label="{ item }">
              <div class="flex flex-col gap-1 text-ink-gray-9">
                <div>{{ item.label }}</div>
                <div class="text-ink-gray-4 text-sm">
                  {{ item.email }}
                </div>
              </div>
            </template>
          </Combobox>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import RichTextField from '@/components/RichTextField.vue'
import EmailSubjectSettings from '@/components/Settings/Profile/EmailSubjectSettings.vue'
import { userEmailSubjects } from '@/composables/emailSubject'
import { isPhone } from '@/composables/phone'
import {
  useSettingsSaveBar,
  useSettingsSubpage,
} from '@/components/Settings/settingsPhone'
import {
  Badge,
  Button,
  Combobox,
  createDocumentResource,
  createListResource,
  toast,
} from 'frappe-ui'
import { computed, inject, ref } from 'vue'

const emit = defineEmits(['updateStep'])

const { user: sessionUser } = inject('session')

const user = createDocumentResource({ doctype: 'User', name: sessionUser })

const emails = createListResource({
  doctype: 'Email Account',
  cache: 'Outgoing Email Accounts',
  fields: ['name', 'email_id'],
  filters: { enable_outgoing: 1 },
  auto: true,
})

const filteredEmails = computed(() => {
  if (!emails.data) return []
  const linkedEmails = user.doc.user_emails?.map((e) => e.email_id) || []
  return emails.data
    .map((doc) => ({
      label: doc.name,
      value: doc.name,
      email: doc.email_id,
    }))
    .filter((e) => !linkedEmails.includes(e.email))
})

const isDirty = computed(() => {
  return JSON.stringify(user.doc) !== JSON.stringify(user.originalDoc)
})

const discards = ref(0)

useSettingsSubpage({
  title: () => __('Email Settings'),
  back: () => emit('updateStep', 'profile-settings'),
})

useSettingsSaveBar({
  isDirty: () => isDirty.value,
  saving: () => user.save.loading,
  save: update,
  discard: () => {
    user.doc = JSON.parse(JSON.stringify(user.originalDoc))
    discards.value++
  },
})

function addEmail(email) {
  if (!user.doc.user_emails) {
    user.doc.user_emails = []
  }
  user.doc.user_emails.push({
    email_account: email.label,
    email_id: email.email,
  })
}

function removeEmail(email) {
  user.doc.user_emails = user.doc.user_emails.filter(
    (e) => e.email_id !== email.email_id,
  )
}

function update() {
  user.save.submit(null, {
    onSuccess: () => {
      userEmailSubjects.reload()
      toast.success(__('Email settings updated successfully'))
    },
  })
}

useKeyboardShortcuts({
  ignoreTyping: false,
  shortcuts: [
    {
      match: (e) => (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's',
      action: () => {
        if (isDirty.value) {
          update()
        }
      },
    },
  ],
})
</script>
