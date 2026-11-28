<template>
  <div
    class="flex items-center justify-between px-2 py-3 border-outline-elevation-2 cursor-pointer hover:bg-surface-sidebar rounded-4 max-sm:min-h-14 max-sm:gap-3 max-sm:rounded-none max-sm:px-4"
  >
    <!-- avatar and name -->
    <div
      class="flex items-center justify-between gap-2 max-sm:min-w-0 max-sm:flex-1 max-sm:justify-start max-sm:gap-3"
    >
      <EmailProviderIcon :logo="emailIcon[emailAccount.service]" />
      <div class="max-sm:min-w-0">
        <div
          class="text-p-base text-ink-gray-8 max-sm:truncate max-sm:text-base-medium max-sm:text-ink-gray-9"
        >
          {{ emailAccount.email_account_name }}
        </div>
        <div class="text-p-sm text-ink-gray-5 max-sm:truncate max-sm:text-sm">
          {{ emailAccount.email_id }}
        </div>
      </div>
    </div>
    <div class="max-sm:flex max-sm:shrink-0 max-sm:items-center max-sm:gap-2">
      <Badge variant="subtle" :label="badgeTitle" theme="gray" />
      <span
        class="lucide-chevron-right size-4 text-ink-gray-4 sm:hidden"
        aria-hidden="true"
      />
    </div>
    <!-- email id -->
  </div>
</template>

<script setup>
import { emailIcon } from './emailConfig'
import EmailProviderIcon from './EmailProviderIcon.vue'
import { computed } from 'vue'

const props = defineProps({
  emailAccount: { type: Object, required: true },
})

const badgeTitle = computed(() => {
  if (
    props.emailAccount.default_incoming &&
    props.emailAccount.default_outgoing
  ) {
    return __('Default Sending & Inbox')
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
