<template>
  <div v-if="isEmoji(icon)" v-bind="$attrs">
    {{ icon }}
  </div>
  <span
    v-else-if="typeof icon == 'string' && icon.startsWith('lucide-')"
    :class="icon"
    aria-hidden="true"
    v-bind="$attrs"
  />
  <FeatherIcon
    v-else-if="typeof icon == 'string'"
    :name="icon"
    v-bind="$attrs"
  />
  <component :is="icon" v-else v-bind="$attrs" />
</template>
<script setup>
import { isEmoji } from '@/utils'

defineProps({ icon: { type: [String, Object], required: true } })
</script>
