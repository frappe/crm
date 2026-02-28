<template>
  <div v-if="isEmoji(icon)" v-bind="$attrs">
    {{ icon }}
  </div>
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
