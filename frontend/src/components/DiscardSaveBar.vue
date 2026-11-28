<!-- The bar at the foot of a phone page with unsaved edits: what is not saved, Discard and Save. -->
<template>
  <div
    class="flex shrink-0 items-center gap-2 border-t border-outline-gray-2 bg-surface-base px-4 py-2.5 pb-[max(0.625rem,env(safe-area-inset-bottom))]"
  >
    <Badge :label="badgeLabel" theme="amber" variant="subtle" />
    <div class="flex-1" />
    <Button
      :label="__('Discard')"
      :disabled="saving"
      @click="emit('discard')"
    />
    <Button
      variant="solid"
      :label="__('Save')"
      :loading="saving"
      @click="emit('save')"
    />
  </div>
</template>

<script setup>
import { Badge, Button } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  /** How many values are not saved; leave at 0 when the page cannot count them. */
  count: { type: Number, default: 0 },
  saving: { type: Boolean, default: false },
})

const emit = defineEmits(['discard', 'save'])

const badgeLabel = computed(() =>
  props.count ? __('{0} not saved', [props.count]) : __('Not saved'),
)
</script>
