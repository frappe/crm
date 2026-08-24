<template>
  <div v-if="isEmoji(icon)" v-bind="$attrs">
    {{ icon }}
  </div>
  <!-- lucide icon from the sprite the IconPicker reads (lucide is a superset of
       feather, so legacy names still resolve). No width/height attrs so size
       classes like `h-4` control it, matching the old FeatherIcon behaviour. -->
  <svg
    v-else-if="typeof icon == 'string'"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="shrink-0"
    v-bind="$attrs"
  >
    <use :href="`#${icon.replace(/^lucide-/, '')}`" />
  </svg>
  <component :is="icon" v-else v-bind="$attrs" />
</template>
<script setup>
import { isEmoji } from '@/utils'

defineProps({ icon: { type: [String, Object], required: true } })
</script>
