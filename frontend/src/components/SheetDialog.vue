<!-- A Dialog on a computer and a BottomSheet on a phone, with the same title, body and #actions. -->
<template>
  <BottomSheet v-if="isPhone" v-model:open="open" :title="title">
    <div class="flex flex-col gap-4 px-4 pb-8">
      <slot />
      <div v-if="$slots.actions" class="pt-2">
        <slot name="actions" />
      </div>
    </div>
  </BottomSheet>
  <Dialog v-else v-model:open="open" :title="title" :size="size">
    <template #default>
      <slot />
    </template>
    <template v-if="$slots.actions" #actions>
      <slot name="actions" />
    </template>
  </Dialog>
</template>

<script setup>
import { isPhone, useBackClose } from '@/composables/phone'
import { BottomSheet, Dialog } from 'frappe-ui'

defineProps({
  title: { type: String, default: '' },
  size: { type: String, default: 'lg' },
})

const open = defineModel('open', { type: Boolean, default: false })

useBackClose(
  () => isPhone.value && open.value,
  () => (open.value = false),
)
</script>
