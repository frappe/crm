<template>
  <!-- markdown is passed through sanitizeHTML() (DOMPurify), so v-html is safe here -->
  <div
    class="flow-answer text-base leading-relaxed text-ink-gray-8"
    @click="onClick"
    v-html="html"
  />
</template>

<script setup>
import { marked } from 'marked'
import { computed } from 'vue'
import router from '@/router'
import { closeCommandPalette } from '@/composables/useCommandPalette'
import { sanitizeHTML } from '@/utils'
import { isPlainClick, linkRecordNames } from './flowAnswer'

const props = defineProps({ text: { type: String, required: true } })

const html = computed(() =>
  sanitizeHTML(
    marked.parse(linkRecordNames(props.text), { gfm: true, async: false }),
  ),
)

// A link to a CRM page opens in place; others open in a new tab. A click with
// Cmd, Ctrl or Shift is the browser's: a new tab or window.
function onClick(event) {
  const link = event.target.closest('a[href]')
  if (!link || !isPlainClick(event)) return
  event.preventDefault()
  const href = link.getAttribute('href')
  if (href.startsWith('/crm/')) {
    closeCommandPalette()
    router.push(href.slice('/crm'.length))
  } else {
    window.open(href, '_blank', 'noopener')
  }
}
</script>

<style>
.flow-answer > * + * {
  margin-top: 0.5rem;
}
.flow-answer ul {
  list-style: disc;
  padding-inline-start: 1.25rem;
}
.flow-answer ol {
  list-style: decimal;
  padding-inline-start: 1.25rem;
}
.flow-answer a {
  text-decoration: underline;
  text-underline-offset: 2px;
}
.flow-answer table {
  font-size: 0.875rem;
}
.flow-answer th,
.flow-answer td {
  padding: 0.25rem 0.75rem 0.25rem 0;
  text-align: start;
  vertical-align: top;
}
.flow-answer code {
  font-size: 0.85em;
}
</style>
