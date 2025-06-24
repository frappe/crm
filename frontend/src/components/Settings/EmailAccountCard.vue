<template>
  <div
    class="flex items-center justify-between p-1 py-3 border-b border-outline-gray-modals cursor-pointer"
  >
    <!-- avatar and name -->
    <div class="flex items-center justify-between gap-2">
      <EmailProviderIcon :logo="emailIcon[emailAccount.service]" />
      <div>
        <p class="text-sm font-semibold text-ink-gray-8">
          {{ emailAccount.email_account_name }}
        </p>
        <div class="text-sm text-ink-gray-4">{{ emailAccount.email_id }}</div>
      </div>
    </div>
    <div>
      <Badge variant="subtle" :label="badgeTitle" theme="gray" />
    </div>
    <!-- email id -->
  </div>
</template>

<script setup>
import { emailIcon } from './emailConfig'
import EmailProviderIcon from './EmailProviderIcon.vue'
import { computed } from 'vue'

const props = defineProps({
  emailAccount: {
    type: Object,
    required: true,
  },
})

const badgeTitle = computed(() => {
  if (
    props.emailAccount.default_incoming &&
    props.emailAccount.default_outgoing
  ) {
    return __('Default Sending and Inbox')
  } else if (props.emailAccount.default_incoming) {
    return __('Default Inbox')
  } else if (props.emailAccount.default_outgoing) {
    return __('Default Sending')
  } else {
    return __('Inbox')
  }
})
</script>

<style scoped></style>
