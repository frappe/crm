<template>
  <template v-for="(part, index) in markedParts(text)" :key="index">
    <mark
      v-if="part.marked"
      class="rounded-1 bg-surface-amber-2 text-ink-gray-8"
      v-text="part.text"
    />
    <template v-else>{{ part.text }}</template>
  </template>
</template>

<script setup>
import { markedParts } from '@/utils/markedText'

defineProps({ text: { type: String, default: '' } })
</script>
