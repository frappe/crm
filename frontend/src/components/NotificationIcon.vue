<template>
  <div
    class="flex size-7 shrink-0 items-center justify-center rounded-full bg-surface-gray-2 text-ink-gray-7"
  >
    <WhatsAppIcon v-if="category === 'whatsapp'" class="size-4" />
    <EmailIcon v-else-if="category === 'emails'" class="size-4" />
    <span v-else :class="icon" class="size-4" aria-hidden="true" />
  </div>
</template>

<script setup>
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import { notificationCategory } from '@/utils/notifications'
import { computed } from 'vue'

const props = defineProps({
  notification: { type: Object, required: true },
})

// Same icons as the category filter, so a row's icon says what kind it is.
const ICONS = {
  mentions: 'lucide-at-sign',
  assignments: 'lucide-user-plus',
  reminders: 'lucide-alarm-clock',
  events: 'lucide-calendar',
}

const category = computed(() => notificationCategory(props.notification))
const icon = computed(() => ICONS[category.value] || 'lucide-bell')
</script>
