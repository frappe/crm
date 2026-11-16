<template>
  <WhatsAppIcon v-if="kind === 'whatsapp'" class="size-7" />
  <div
    v-else-if="kind"
    class="flex size-7 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-7"
  >
    <EmailIcon v-if="kind === 'email'" class="size-4" />
    <span v-else class="lucide-alarm-clock size-4" aria-hidden="true" />
  </div>
  <UserAvatar v-else :user="notification.from_user.name" size="lg" />
</template>

<script setup>
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { computed } from 'vue'

const props = defineProps({
  notification: { type: Object, required: true },
})

const kind = computed(() => {
  const { type, notification_type_doctype } = props.notification
  if (type === 'WhatsApp') return 'whatsapp'
  if (type === 'Reminder') return 'reminder'
  if (type !== 'Reply') return null
  return notification_type_doctype === 'WA Message' ? 'whatsapp' : 'email'
})
</script>
