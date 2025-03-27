<template>
  <div class="flex items-center justify-between p-1 border-b border-gray-200 cursor-pointer">
    <!-- avatar and name -->
    <div class="flex items-center justify-between gap-2">
      <EmailProviderIcon :logo="emailIcon[emailAccount.service]" />
      <div>
        <p class="text-sm font-semibold text-gray-700">
          {{ emailAccount.email_account_name }}
        </p>
        <div class="text-sm text-gray-500">{{ emailAccount.email_id }}</div>
      </div>
    </div>
    <div>
      <Badge variant="subtle" :label="badgeTitleColor[0]" :theme="badgeTitleColor[1]" />
    </div>
    <!-- email id -->
  </div>
</template>

<script setup>
import { emailIcon } from "./emailConfig";
import EmailProviderIcon from "./EmailProviderIcon.vue";
import { computed } from "vue";

const props = defineProps({
  emailAccount: {
    type: Object,
    required: true
  }
});

const badgeTitleColor = computed(() => {
  if (
    props.emailAccount.default_incoming &&
    props.emailAccount.default_outgoing
  ) {
    const color =
      props.emailAccount.enable_incoming && props.emailAccount.enable_outgoing
        ? "blue"
        : "gray";
    return ["Default Sending and Inbox", color];
  } else if (props.emailAccount.default_incoming) {
    const color = props.emailAccount.enable_incoming ? "blue" : "gray";
    return ["Default Inbox", color];
  } else if (props.emailAccount.default_outgoing) {
    const color = props.emailAccount.enable_outgoing ? "blue" : "gray";
    return ["Default Sending", color];
  } else {
    const color = props.emailAccount.enable_incoming ? "blue" : "gray";
    return ["Inbox", color];
  }
});
</script>

<style scoped></style>
