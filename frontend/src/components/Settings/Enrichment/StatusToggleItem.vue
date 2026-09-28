<template>
  <div
    class="flex h-7 w-full cursor-pointer items-center gap-2 rounded px-2 text-base text-ink-gray-7 hover:bg-surface-gray-3 focus:bg-surface-gray-3 focus:outline-none"
  >
    <LucideCircleCheck class="size-4 shrink-0" />
    <span class="flex-1 whitespace-nowrap">{{ __('Status') }}</span>
    <!-- Display only: the whole row is the menu item, so a click anywhere on
         it (the switch included) reaches the item's select handler once. A
         live Switch would toggle itself and then be toggled back by the row. -->
    <Switch
      size="sm"
      :model-value="enabled"
      tabindex="-1"
      class="pointer-events-none"
    />
  </div>
</template>

<script setup>
import { Switch } from 'frappe-ui'
import LucideCircleCheck from '~icons/lucide/circle-check'

// The "Status" row of an enrichment rule's ⋯ menu. The toggle itself is the
// menu option's onClick (see EnrichmentRuleMenu.vue), which keeps the menu
// open; this only draws the row.
defineProps({
  enabled: { type: Boolean, default: false },
})
</script>
