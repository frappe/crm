<template>
  <Badge :label="status" :theme="theme" variant="subtle" size="md" />
</template>

<script setup>
import { computed } from 'vue'
import { Badge } from 'frappe-ui'

const props = defineProps({
  status: { type: String, default: '' },
})

// Map document statuses -> frappe-ui Badge themes (gray|blue|green|red|amber…).
const THEME_MAP = {
  Paid: 'green',
  Approved: 'green',
  Confirmed: 'green',
  Completed: 'green',
  Reconciled: 'green',
  Submitted: 'blue',
  Reported: 'blue',
  Open: 'blue',
  Unpaid: 'amber',
  'Partly Paid': 'amber',
  Pending: 'amber',
  Draft: 'gray',
  Unreconciled: 'amber',
  Overdue: 'red',
  Rejected: 'red',
  Cancelled: 'red',
  Return: 'red',
}

const theme = computed(() => THEME_MAP[props.status] || 'gray')
</script>
