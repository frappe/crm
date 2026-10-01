<template>
  <Dropdown placement="right" :options="options">
    <Button
      icon="lucide-more-horizontal"
      variant="ghost"
      :disabled="disabled"
      @click="isConfirmingDelete = false"
    />
  </Dropdown>
</template>

<script setup>
import { Button, Dropdown } from 'frappe-ui'
import { ConfirmDelete, TemplateOption } from '@/utils'
import { computed, ref } from 'vue'

// Delete only flags the row; the header Update sends it, so leaving without
// saving undoes it.
const props = defineProps({
  // A just-added empty row has nothing to lose, so it gets a one-step Delete.
  blank: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['delete'])

// Reset on every open so the menu always starts at the grey Delete step.
const isConfirmingDelete = ref(false)

const options = computed(() => {
  if (props.blank) {
    // TemplateOption so it matches ConfirmDelete's grey first step.
    return [
      {
        label: __('Delete'),
        component: (itemProps) =>
          TemplateOption({
            option: __('Delete'),
            icon: 'trash-2',
            active: itemProps.active,
            onClick: () => emit('delete'),
          }),
      },
    ]
  }

  return ConfirmDelete({
    isConfirmingDelete,
    onConfirmDelete: () => emit('delete'),
  })
})
</script>
