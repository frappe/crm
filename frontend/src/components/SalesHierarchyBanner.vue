<template>
  <div
    v-if="!isSidebarCollapsed"
    class="flex flex-col gap-3 shadow-sm rounded-lg py-2.5 px-3 bg-surface-modal text-base"
  >
    <div class="inline-flex text-ink-gray-9 gap-2 items-center font-medium">
      <FeatherIcon class="h-4" name="info" />
      {{ __('Sales Hierarchy') }}
    </div>
    <div class="text-ink-gray-7 text-p-sm">
      {{ __('TODO: Write a short message') }}
    </div>
    <Button :label="__('Learn more')" @click="openBlog">
      <template #suffix>
        <FeatherIcon class="h-3.5" name="external-link" />
      </template>
    </Button>
  </div>
</template>

<script setup>
import { Button, FeatherIcon } from 'frappe-ui'

defineProps({
  isSidebarCollapsed: {
    type: Boolean,
    default: false,
  },
})

const BLOG_URL = ''

function openBlog() {
  if (!BLOG_URL) return
  window.open(BLOG_URL, '_blank', 'noopener')
}
</script>
