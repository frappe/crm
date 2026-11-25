<!-- Help at the end of the avatar row. With notices it gets a dot, and opens them on click or hover. -->
<template>
  <a
    v-if="!notices.length"
    :href="DOCS_URL"
    target="_blank"
    rel="noopener"
    :class="BUTTON"
    :aria-label="__('Help')"
    :title="__('Help')"
  >
    <span class="lucide-circle-help size-4" aria-hidden="true" />
  </a>
  <Popover
    v-else
    v-model:open="open"
    side="right"
    align="end"
    :offset="12"
    :autoFocus="false"
  >
    <template #trigger>
      <button
        type="button"
        :class="[BUTTON, open && 'bg-surface-gray-3']"
        :aria-label="__('Help and notices')"
        @pointerenter="hover(true)"
        @pointerleave="hover(false)"
      >
        <span class="lucide-circle-help size-4" aria-hidden="true" />
        <span
          class="absolute right-1 top-1 size-1.5 rounded-full ring-2 ring-[var(--surface-gray-1)]"
          :class="DOT[level]"
        />
      </button>
    </template>
    <template #default>
      <div
        class="flex w-72 flex-col gap-1.5 p-1.5"
        @pointerenter="hover(true)"
        @pointerleave="hover(false)"
      >
        <SidebarCard
          v-for="notice in notices"
          :key="notice.key"
          :theme="notice.theme"
          :title="notice.title"
          :description="notice.description"
          :dismissible="notice.dismissible"
          :action="notice.action"
          @dismiss="notice.onDismiss"
        />
        <div class="mx-1.5 border-t border-outline-gray-2" />
        <a
          :href="DOCS_URL"
          target="_blank"
          rel="noopener"
          class="flex h-7 items-center gap-2 rounded-4 px-2 text-base text-ink-gray-8 hover:bg-surface-gray-2"
        >
          <span
            class="lucide-book-open size-4 text-ink-gray-6"
            aria-hidden="true"
          />
          <span class="flex-1">{{ __('Documentation') }}</span>
          <span
            class="lucide-external-link size-3.5 text-ink-gray-5"
            aria-hidden="true"
          />
        </a>
      </div>
    </template>
  </Popover>
</template>

<script setup>
import { useSidebarNotices } from '@/composables/sidebarNotices'
import { Popover, SidebarCard } from 'frappe-ui'
import { onUnmounted, ref } from 'vue'

const DOCS_URL = 'https://docs.frappe.io/crm'
const BUTTON =
  'relative grid size-7 shrink-0 place-items-center rounded-4 text-ink-gray-6 transition hover:bg-surface-gray-2 focus-visible:ring-0 focus-visible:focus-ring'
const DOT = {
  info: 'bg-surface-gray-9',
  soon: 'bg-surface-amber-6',
  urgent: 'bg-surface-red-6',
}
const OPEN_DELAY = 300
const CLOSE_DELAY = 200

const { notices, level } = useSidebarNotices()
const open = ref(false)

// Hovering opens after a pause and stays open while the pointer is on the icon or the panel.
let timer = null
function hover(entering) {
  clearTimeout(timer)
  if (entering === open.value) return
  timer = setTimeout(
    () => (open.value = entering),
    entering ? OPEN_DELAY : CLOSE_DELAY,
  )
}
onUnmounted(() => clearTimeout(timer))
</script>
