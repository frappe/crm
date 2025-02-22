<template>
  <Dialog
    v-model="show"
    :options="{
      title: __('Unsaved Changes'),
      size: 'sm',
      actions: [
        {
          label: __('Cancel'),
          variant: 'subtle',
          onClick: () => {
            show = false
            emit('cancel')
          },
        },
        {
          label: __('Close Without Saving'),
          variant: 'danger',
          onClick: () => {
            show = false
            emit('confirm')
          },
        },
      ],
    }"
  >
    <template #body-content>
      <div class="text-base text-ink-gray-7">
        {{ __('You have unsaved changes. Are you sure you want to close this window?') }}
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { Dialog } from 'frappe-ui'

const show = defineModel()
const emit = defineEmits(['confirm', 'cancel'])
</script> 