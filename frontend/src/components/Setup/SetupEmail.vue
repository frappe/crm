<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Connect your email') }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{
        __(
          'Send and receive email from the CRM, and keep every conversation on the right lead or deal.',
        )
      }}
    </p>
    <EmailAdd
      :key="formKey"
      class="mt-6 flex-1"
      hide-header
      @created="emit('done')"
      @update:step="formKey++"
    />
    <Button
      variant="ghost"
      class="mt-6 self-center"
      :label="__('I\'ll set this up later')"
      @click="showSkipDialog = true"
    />

    <Dialog
      v-model="showSkipDialog"
      :options="{ title: __('Continue with fewer features?') }"
    >
      <template #body-content>
        <p class="text-p-base text-ink-gray-6">
          {{ __('Without a connected email account you will miss out on:') }}
        </p>
        <ul class="mt-3 flex flex-col gap-2 rounded-lg bg-surface-gray-1 p-3">
          <li
            v-for="feature in missedFeatures"
            :key="feature.label"
            class="flex items-center gap-2 text-base text-ink-gray-8"
          >
            <component :is="feature.icon" class="size-4 text-ink-gray-5" />
            {{ feature.label }}
          </li>
        </ul>
      </template>
      <template #actions>
        <div class="flex justify-end gap-2">
          <Button :label="__('Cancel')" @click="showSkipDialog = false" />
          <Button
            variant="solid"
            theme="red"
            :label="__('Yes, skip')"
            @click="confirmSkip"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import LucideMail from '~icons/lucide/mail'
import LucideSend from '~icons/lucide/send'
import LucideUserPlus from '~icons/lucide/user-plus'
import EmailAdd from '@/components/Settings/EmailAdd.vue'
import { Button, Dialog } from 'frappe-ui'
import { ref } from 'vue'

const emit = defineEmits(['done', 'skip'])

const formKey = ref(0)
const showSkipDialog = ref(false)

const missedFeatures = [
  { icon: LucideMail, label: __('Emails logged on leads and deals') },
  { icon: LucideSend, label: __('Sending and replying from the CRM') },
  { icon: LucideUserPlus, label: __('Leads created from incoming email') },
]

function confirmSkip() {
  showSkipDialog.value = false
  emit('skip')
}
</script>
