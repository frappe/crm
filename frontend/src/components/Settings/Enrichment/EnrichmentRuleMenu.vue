<template>
  <Dropdown placement="right" :options="options">
    <Button
      icon="lucide-more-horizontal"
      variant="ghost"
      @click="isConfirmingDelete = false"
    />
  </Dropdown>
</template>

<script setup>
import { Button, Dropdown } from 'frappe-ui'
import { ConfirmDelete } from '@/utils'
import { ref } from 'vue'

// The per-row ⋯ menu. Its Delete asks first by swapping itself for "Confirm
// Delete", which is how every other Settings list confirms (see
// SlaPriorityList.vue). The flag is per menu, and reset when the menu is opened,
// so a row left mid-confirmation doesn't reopen already asking.
const emit = defineEmits(['delete'])

const isConfirmingDelete = ref(false)

// Dropdown re-evaluates each option's `condition` as it renders, so the array
// itself is built once and still flips between Delete and Confirm Delete.
const options = ConfirmDelete({
  isConfirmingDelete,
  onConfirmDelete: () => emit('delete'),
})
</script>
