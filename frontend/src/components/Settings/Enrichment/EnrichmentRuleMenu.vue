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
// the menu opens), with the menu's own red theme on both steps.
const isConfirmingDelete = ref(false)

const options = computed(() => {
  if (props.blank) {
    return [
      {
        label: __('Delete'),
        icon: 'trash-2',
        theme: 'red',
        onClick: () => emit('delete'),
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
    {
      label: __('Delete'),
      icon: 'trash-2',
      theme: 'red',
      condition: () => !isConfirmingDelete.value,
      onClick: (event) => {
        event.preventDefault()
        isConfirmingDelete.value = true
      },
    },
    {
      label: __('Confirm Delete'),
      icon: 'trash-2',
      theme: 'red',
      condition: () => isConfirmingDelete.value,
      onClick: () => {
        isConfirmingDelete.value = false
        emit('delete')
      },
    },
  ]
})
</script>
