<template>
  <div class="html-control text-sm text-ink-gray-8" v-html="sanitizedHtml" />
</template>

<script setup>
import { computed } from 'vue'
import DOMPurify from 'dompurify'

const props = defineProps({
  html: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const sanitizedHtml = computed(() => {
  if (!props.html) return ''
  return DOMPurify.sanitize(props.html)
})
</script>
