<template>
  <div
    v-if="display.data"
    class="text-p-sm text-ink-gray-7 [&_br:last-child]:hidden"
  >
    <!-- content is passed through sanitizeHTML() (DOMPurify) before rendering, so v-html is safe here -->
    <!-- eslint-disable vue/no-v-html -->
    <div v-html="sanitizeHTML(display.data)" />
    <!-- eslint-enable vue/no-v-html -->
  </div>
</template>

<script setup>
import { sanitizeHTML } from '@/utils'
import { createResource } from 'frappe-ui'
import { watch } from 'vue'

const props = defineProps({
  name: { type: String, default: '' },
})

// The Address Template is admin-editable, so the rendered block is fetched
// rather than assembled here; sanitizeHTML() guards what comes back.
const display = createResource({
  url: 'crm.api.address.get_address_display',
  makeParams: () => ({ name: props.name }),
  auto: Boolean(props.name),
})

watch(
  () => props.name,
  (name) => {
    if (name) {
      display.fetch()
    } else {
      display.data = null
    }
  },
)
</script>
