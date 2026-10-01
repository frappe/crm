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

// The per-row ⋯ menu. Delete writes nothing: it only marks the row on screen,
// and the header Update sends it along with every other rule edit -- so leaving
// the page without saving is the undo.
const props = defineProps({
  // A row that was just added and has nothing typed into it. It has nothing to
  // lose, so its menu is a bare Delete.
  blank: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['delete'])

// The same two-step delete AssignmentRuleListItem.vue uses (reset each time
// the menu opens): a grey Delete, then a red Confirm Delete.
const isConfirmingDelete = ref(false)

const options = computed(() => {
  if (props.blank) {
    // Drawn like ConfirmDelete's first step, so it reads the same grey.
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
