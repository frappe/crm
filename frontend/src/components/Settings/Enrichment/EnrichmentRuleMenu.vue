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
import { computed, h, ref } from 'vue'
import StatusToggleItem from './StatusToggleItem.vue'

// The per-row ⋯ menu. Neither item writes anything: the status toggle and the
// delete only change the row on screen, and the header Save sends them along
// with every other rule edit -- so leaving the page without saving is the undo.
const props = defineProps({
  enabled: { type: Boolean, default: false },
  // A row that was just added and has nothing typed into it. It has no status
  // worth setting and nothing to lose, so its menu is a bare Delete.
  blank: { type: Boolean, default: false },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['toggle', 'delete'])

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

  return [
    {
      label: __('Status'),
      component: () => h(StatusToggleItem, { enabled: props.enabled }),
      // preventDefault keeps the Dropdown open, so the switch can be seen
      // flipping and flipped back.
      onClick: (event) => {
        event.preventDefault()
        emit('toggle')
      },
    },
    ...ConfirmDelete({
      isConfirmingDelete,
      onConfirmDelete: () => emit('delete'),
    }),
  ]
})
</script>
