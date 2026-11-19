<template>
  <div class="flex items-center justify-between gap-2 px-4 pb-2">
    <TabButtons v-model="read" :options="readOptions" />
    <Dropdown :options="categoryOptions" align="end">
      <Button
        :label="current.label"
        icon-left="lucide-list"
        icon-right="lucide-chevron-down"
      />
    </Dropdown>
  </div>
</template>
<script setup lang="ts">
import type { NotificationCategory } from '@/utils/notifications'
import { Button, Dropdown, TabButtons } from 'frappe-ui'
import { computed } from 'vue'

const read = defineModel<'all' | 'unread'>('read', { required: true })
const category = defineModel<NotificationCategory | ''>('category', {
  required: true,
})

const readOptions = [
  { label: __('All'), value: 'all' },
  { label: __('Unread'), value: 'unread' },
]

const categories: {
  label: string
  value: NotificationCategory | ''
  icon: string
}[] = [
  { label: __('All categories'), value: '', icon: 'lucide-list' },
  { label: __('Emails'), value: 'emails', icon: 'lucide-mail' },
  { label: __('WhatsApp'), value: 'whatsapp', icon: 'lucide-message-circle' },
  { label: __('Mentions'), value: 'mentions', icon: 'lucide-at-sign' },
  { label: __('Assignments'), value: 'assignments', icon: 'lucide-user-plus' },
  { label: __('Reminders'), value: 'reminders', icon: 'lucide-alarm-clock' },
  { label: __('Events'), value: 'events', icon: 'lucide-calendar' },
]

const categoryOptions = categories.map((c) => ({
  label: c.label,
  icon: c.icon,
  onClick: () => (category.value = c.value),
}))

const current = computed(
  () => categories.find((c) => c.value === category.value) || categories[0],
)
</script>
