<template>
  <div
    class="inline-flex items-center gap-0.5 text-sm"
    :class="{
      'bg-surface-gray-2 rounded-sm text-ink-gray-5 py-0.5 px-1': bg,
      'text-ink-gray-4': !bg,
    }"
  >
    <span v-if="ctrl || meta">
      <LucideCommand v-if="isMac" class="w-3 h-3" />
      <span v-else>Ctrl</span>
    </span>
    <span v-if="shift"><LucideShift class="w-3 h-3" /></span>
    <span v-if="alt"><LucideAlt class="w-3 h-3" /></span>
    <slot></slot>
  </div>
</template>
<script setup>
import LucideCommand from '~icons/lucide/command'
import LucideShift from '~icons/lucide/arrow-big-up'
import LucideAlt from '~icons/lucide/option'

const isMac = navigator.userAgent.includes('Mac')

defineProps({
  meta: Boolean,
  ctrl: Boolean,
  shift: Boolean,
  alt: Boolean,
  shortcut: String,
  bg: Boolean,
})
</script>
