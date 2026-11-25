<!--
  The notices above the avatar, as a stack: the most urgent card in front and up to two edges
  behind it. Hover or tap fans the stack out. In the collapsed sidebar it is an icon that opens
  the cards beside the sidebar.
-->
<template>
  <Popover v-if="isCollapsed && front" side="right" align="end" :offset="12">
    <template #trigger>
      <button
        type="button"
        class="relative mx-0.5 grid size-7 place-items-center rounded-4 transition hover:opacity-80 focus-visible:ring-0 focus-visible:focus-ring"
        :class="TINT[front.theme]"
        :aria-label="__('Notices')"
      >
        <span :class="ICON[front.theme]" class="size-4" aria-hidden="true" />
        <span
          v-if="notices.length > 1"
          class="absolute -right-1.5 -top-1.5 grid h-3.5 min-w-3.5 place-items-center rounded-full bg-surface-gray-9 px-1 text-[10px] font-semibold leading-none text-ink-white"
        >
          {{ notices.length }}
        </span>
      </button>
    </template>
    <template #default>
      <div class="flex w-64 flex-col gap-1.5 p-1.5">
        <SidebarCard
          v-for="notice in notices"
          :key="notice.key"
          v-bind="cardProps(notice)"
          @dismiss="notice.onDismiss"
        />
      </div>
    </template>
  </Popover>

  <div
    v-else-if="front"
    ref="stack"
    class="relative w-56 shrink-0"
    @pointerenter="hover(true)"
    @pointerleave="hover(false)"
    @click="expanded = canExpand"
  >
    <!-- Fanned out, the cards open over the views instead of pushing them up. -->
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="translate-y-3 opacity-0"
      leave-active-class="transition duration-300 ease-in"
      leave-to-class="translate-y-3 opacity-0"
    >
      <div
        v-if="expanded"
        class="absolute inset-x-0 bottom-0 z-10 flex flex-col gap-1.5 bg-surface-gray-1 pt-1.5"
      >
        <SidebarCard
          v-for="notice in fannedOut"
          :key="notice.key"
          v-bind="cardProps(notice)"
          @dismiss="notice.onDismiss"
        />
      </div>
    </Transition>
    <!-- Kept while fanned out, so the sidebar foot keeps its height. -->
    <div
      class="relative"
      :class="expanded && 'invisible'"
      :style="{ paddingTop: `${edges * EDGE}px` }"
    >
      <div
        v-for="edge in edges"
        :key="edge"
        class="absolute h-10 rounded-6 border border-outline-alpha-gray-1 bg-surface-base"
        :style="edgeStyle(edge)"
        aria-hidden="true"
      />
      <SidebarCard
        class="relative"
        v-bind="
          front.urgent
            ? cardProps(front)
            : { theme: front.theme, title: front.title }
        "
        @dismiss="front.onDismiss"
      />
    </div>
  </div>
</template>

<script setup>
import { useSidebarNotices } from '@/composables/sidebarNotices'
import { onClickOutside } from '@vueuse/core'
import { Popover, SidebarCard } from 'frappe-ui'
import { computed, onUnmounted, ref } from 'vue'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

// The stack keeps the open sidebar's inner width (w-56), so while the sidebar's
// width animates the cards are uncovered instead of rewrapping.
const EDGE = 6
const MAX_EDGES = 2
const OPEN_DELAY = 150
const CLOSE_DELAY = 250
const TINT = {
  gray: 'bg-surface-gray-3 text-ink-gray-7',
  blue: 'bg-surface-gray-3 text-ink-gray-7',
  amber: 'bg-surface-amber-2 text-ink-amber-7',
  red: 'bg-surface-red-2 text-ink-red-7',
}
const ICON = {
  gray: 'lucide-circle-alert',
  blue: 'lucide-circle-alert',
  amber: 'lucide-triangle-alert',
  red: 'lucide-circle-x',
}

const { notices } = useSidebarNotices()
const front = computed(() => notices.value[0])
const edges = computed(() => Math.min(notices.value.length - 1, MAX_EDGES))
// Fanned out, the most urgent card stays nearest the avatar.
const fannedOut = computed(() => notices.value.slice().reverse())

// A lone urgent notice already shows its whole card, so there is nothing to fan out.
const canExpand = computed(
  () => notices.value.length > 1 || !front.value?.urgent,
)
const expanded = ref(false)
const stack = ref(null)
onClickOutside(stack, () => (expanded.value = false))

function cardProps(notice) {
  return {
    theme: notice.theme,
    title: notice.title,
    description: notice.description,
    dismissible: notice.dismissible,
    action: notice.action,
  }
}

// Edge 1 sits just behind the front card, edge 2 behind and above it.
function edgeStyle(edge) {
  const inset = `${edge * EDGE}px`
  return { top: `${(edges.value - edge) * EDGE}px`, left: inset, right: inset }
}

let timer = null
function hover(entering) {
  clearTimeout(timer)
  if (entering === expanded.value || (entering && !canExpand.value)) return
  timer = setTimeout(
    () => (expanded.value = entering),
    entering ? OPEN_DELAY : CLOSE_DELAY,
  )
}
onUnmounted(() => clearTimeout(timer))
</script>
