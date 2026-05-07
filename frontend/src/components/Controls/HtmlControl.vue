<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div class="html-control text-sm text-ink-gray-8" v-html="sanitizedHtml" />
</template>

<script setup>
import { sanitizeHTML } from '@/utils'
import { computed } from 'vue'

const props = defineProps({
  html: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const sanitizedHtml = computed(() => {
  if (!props.html) return ''
  return sanitizeHTML(props.html)
})
</script>
