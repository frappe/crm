<template>
  <div class="html-control text-sm text-ink-gray-8" v-html="sanitizedHtml" />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  html: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
})

const sanitizedHtml = computed(() => {
  if (!props.html) return ''
  const parser = new DOMParser()
  const doc = parser.parseFromString(props.html, 'text/html')
  doc.querySelectorAll('script').forEach((el) => el.remove())
  doc.querySelectorAll('*').forEach((el) => {
    Array.from(el.attributes).forEach((attr) => {
      const name = attr.name.toLowerCase()
      if (name.startsWith('on')) {
        el.removeAttribute(attr.name)
      } else if (
        name === 'href' &&
        attr.value.toLowerCase().trim().startsWith('javascript:')
      ) {
        el.removeAttribute(attr.name)
      }
    })
  })
  return doc.body.innerHTML
})
</script>
