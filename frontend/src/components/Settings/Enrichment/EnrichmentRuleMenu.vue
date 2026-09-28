<template>
  <Dropdown placement="right" :options="options">
    <Button icon="lucide-more-horizontal" variant="ghost" />
  </Dropdown>
</template>

<script setup>
import { Button, Dropdown } from 'frappe-ui'

// The per-row ⋯ menu. Delete removes the row straight away without asking: the
// rule is only deleted on the server when the header Save runs, so leaving the
// page without saving is the undo.
const emit = defineEmits(['delete'])

const options = [
  {
    label: __('Delete'),
    icon: 'trash-2',
    onClick: () => emit('delete'),
  },
]
</script>
