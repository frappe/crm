<template>
  <!-- Sized and highlighted like frappe-ui's own menu rows (ItemListRow sm +
       getMenuBackgroundColor), so it sits flush with Delete. reka puts
       data-highlighted on this root while the item has keyboard focus. -->
  <div
    class="flex min-h-7 w-full cursor-pointer items-center gap-2 rounded px-2 py-1.5 outline-none focus:bg-surface-alpha-gray-2 data-[highlighted]:bg-surface-alpha-gray-2"
  >
    <LucideCircleCheck class="size-4 shrink-0 text-ink-gray-6" />
    <span class="whitespace-nowrap text-base text-ink-gray-7">
      {{ __('Status') }}
    </span>
    <!-- Display only: the whole row is the menu item, so a click anywhere on
         it (the switch included) reaches the item's select handler once. A
         live Switch would toggle itself and then be toggled back by the row. -->
    <Switch
      size="sm"
      :model-value="enabled"
      tabindex="-1"
      class="pointer-events-none ml-auto"
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
