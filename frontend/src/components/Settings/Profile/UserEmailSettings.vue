<template>
  <SettingsLayoutBase v-if="user.doc">
    <template #title>
      <div class="flex gap-1 items-center">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="__('Email Settings')"
          size="md"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-xl hover:opacity-70 !pr-0 !max-w-96 !justify-start"
          @click="emit('updateStep', 'profile-settings')"
        />
        <Badge
          v-if="isDirty"
          :label="__('Not Saved')"
          variant="subtle"
          theme="orange"
        />
      </div>
    </template>
    <template #header-actions>
      <Button
        v-if="isDirty"
        variant="solid"
        :label="__('Update')"
        @click="update"
      />
    </template>
    <template #content>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __('Signature') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{ __('Manage your email signature') }}
          </span>
        </div>
        <TextEditor
          editor-class="prose-sm min-h-28 max-w-full border rounded-b-lg border-t-0 p-2 border-outline-gray-modals"
          :content="user.doc.email_signature"
          placeholder="Type something..."
          :bubbleMenu="true"
          :fixed-menu="true"
          @change="(val) => (user.doc.email_signature = val)"
        />
      </div>
      <div class="flex flex-col gap-4 mt-6">
        <div class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">
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
            class="w-full border rounded-md mb-2 border-outline-gray-modals"
          >
            <div
              class="grid grid-cols-[4fr_4fr_0.3fr] gap-2 px-4 py-3 text-sm font-medium text-ink-gray-5 border-b border-outline-gray-modals"
            >
              <span>{{ __('Email Account') }}</span>
              <span>{{ __('Email') }}</span>
              <span></span>
            </div>
            <div
              v-for="e in user.doc.user_emails"
              :key="e.name"
              class="grid grid-cols-[4fr_4fr_0.3fr] gap-2 group items-center px-4 py-2.5 text-base border-b border-outline-gray-modals last:border-b-0"
            >
              <span class="text-ink-gray-8 font-medium truncate">
                {{ e.email_account }}
              </span>
              <span class="text-ink-gray-6 truncate">{{ e.email_id }}</span>
              <div class="group-hover:opacity-100 opacity-0 transition-opacity">
                <Button
                  class="w-10"
                  variant="ghost"
                  :tooltip="__('Remove')"
                  icon="x"
                  @click.prevent="removeEmail(e)"
                />
              </div>
            </div>
          </div>
          <Autocomplete
            value=""
            :options="filteredEmails"
            @change="(e) => addEmail(e)"
          >
            <template #target="{ togglePopover }">
              <Button
                class="!bg-surface-modal"
                variant="outline"
                :label="__('Add Email')"
                iconLeft="plus"
                @click="togglePopover()"
              />
            </template>
            <template #item-label="{ option }">
              <div class="flex flex-col gap-1 text-ink-gray-9">
                <div>{{ option.label }}</div>
                <div class="text-ink-gray-4 text-sm">
                  {{ option.email }}
                </div>
              </div>
            </template>
          </Autocomplete>
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
</template>
<script setup>
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import {
  Badge,
  Button,
  createDocumentResource,
  createListResource,
  TextEditor,
  toast,
} from 'frappe-ui'
import { computed, inject } from 'vue'

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
