<template>
  <div
    class="flex cursor-grab items-center justify-between gap-6 rounded px-2 py-1.5 text-base text-gray-800 hover:bg-gray-100"
  >
    <div class="flex items-center gap-2">
      <DragIcon class="h-3.5" />
      <div>{{ column.label }}</div>
    </div>
    <div class="flex cursor-pointer items-center gap-1">
      <Button
        variant="ghost"
        class="!h-5 w-5 !p-1"
        @click="emit('edit', column)"
      >
        <EditIcon class="h-3.5" />
      </Button>
      <Button
        variant="ghost"
        class="!h-5 w-5 !p-1"
        @click="emit('remove', column)"
      >
        <FeatherIcon name="x" class="h-3.5" />
      </Button>
    </div>
  </div>
</template>
<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import DragIcon from '@/components/Icons/DragIcon.vue'
import { watchDebounced } from '@vueuse/core'

const props = defineProps({
  column: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['edit', 'remove', 'update'])

watchDebounced(
  () => props.column.width,
  (val, old_val) => {
    val = val.replace(/[^\d.]/g, '')
    old_val = old_val.replace(/[^\d.]/g, '')
    if (Math.abs(val - old_val) > 1) return
    emit('update')
  },
  { debounce: 1000 }
)
</script>
