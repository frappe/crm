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
          class="absolute -right-1 -top-1 grid h-3 min-w-3 place-items-center rounded-full bg-surface-gray-9 px-0.5 text-[9px] font-semibold leading-none text-ink-base ring-2 ring-[var(--surface-gray-1)]"
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

  <!-- The foot keeps the folded height, and the cards grow upward over the views. -->
  <div
    v-else-if="front"
    ref="stack"
    class="relative w-56 shrink-0 transition-[height] duration-300"
    :style="{ height: `${foldedHeight}px` }"
    @pointerenter="hover(true)"
    @pointerleave="hover(false)"
    @click="expanded = canExpand"
  >
    <div
      class="absolute inset-x-0 bottom-0 z-10 flex flex-col bg-surface-gray-1"
    >
      <div
        v-for="(notice, index) in backToFront"
        :key="notice.key"
        class="overflow-hidden border border-outline-alpha-gray-1 bg-surface-base transition-all duration-300 ease-out [&>[data-slot=sidebar-card]]:rounded-none [&>[data-slot=sidebar-card]]:border-0 [&_[data-slot]]:transition-opacity [&_[data-slot]]:duration-300"
        :class="[
          isEdge(notice) ? 'rounded-t-6 border-b-0' : 'rounded-6',
          isCompact(notice) && COMPACT,
        ]"
        :style="cardStyle(notice, backToFront.length - 1 - index)"
      >
        <SidebarCard
          :ref="(card) => measure(notice.key, card)"
          v-bind="cardProps(notice)"
          @dismiss="notice.onDismiss"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { useSidebarNotices } from '@/composables/sidebarNotices'
import { onClickOutside } from '@vueuse/core'
import { Popover, SidebarCard } from 'frappe-ui'
import { computed, onUnmounted, reactive, ref } from 'vue'

defineProps({
  isCollapsed: { type: Boolean, default: false },
})

// The stack keeps the open sidebar's inner width (w-56), so while the sidebar's
// width animates the cards are uncovered instead of rewrapping.
// A compact card hides everything below its title row; the parts fade as it opens.
// Its hidden dismiss button gives back the space it reserves, so the title stays on one line.
// The wrapper, not the clipped card, draws the border, so a compact card keeps its bottom edge.
const COMPACT =
  '[&_[data-slot=actions]]:opacity-0 [&_[data-slot=description]]:opacity-0 [&_[data-slot=dismiss]]:opacity-0 [&_div:has(>[data-slot=title])]:pr-0'
const EDGE = 6
const BORDER = 2
const GAP = 6
const STAGGER = 40
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
// Top to bottom: the most urgent card sits nearest the avatar.
const backToFront = computed(() => notices.value.slice().reverse())

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

// Each card always renders whole; its wrapper's height shows all of it, only its title
// row (a compact card) or only its top edge (a card behind). Animating that height is
// the fan-out, so nothing is swapped or re-rendered.
const heights = reactive({})
const observer = new ResizeObserver((entries) => {
  for (const { target } of entries) {
    const row = target.querySelector('[data-slot=title]')?.parentElement
    // Wrapper heights: the card plus the wrapper's top and bottom border.
    heights[target.dataset.notice] = {
      full: target.offsetHeight + BORDER,
      // The title row plus the card's padding below it.
      compact:
        (row ? row.offsetTop + row.offsetHeight + 12 : target.offsetHeight) +
        BORDER,
    }
  }
})
const observed = {}
function measure(key, card) {
  const element = card?.$el
  if (!element || observed[key] === element) return
  if (observed[key]) observer.unobserve(observed[key])
  element.dataset.notice = key
  observer.observe(element)
  observed[key] = element
}
onUnmounted(() => observer.disconnect())

const isEdge = (notice) => !expanded.value && notice !== front.value
const isCompact = (notice) =>
  !expanded.value && notice === front.value && !notice.urgent

function foldedCardHeight(notice) {
  const height = heights[notice.key]
  if (!height) return undefined
  return notice.urgent ? height.full : height.compact
}

const foldedHeight = computed(() => {
  const frontHeight = front.value && foldedCardHeight(front.value)
  return frontHeight === undefined
    ? undefined
    : frontHeight + edges.value * EDGE
})

// `depth` is 0 for the front card, 1 for the card behind it, and so on.
function cardStyle(notice, depth) {
  const height = heights[notice.key]
  if (expanded.value) {
    return {
      height: height && `${height.full}px`,
      marginBottom: depth ? `${GAP}px` : 0,
      transitionDelay: `${depth * STAGGER}ms`,
    }
  }
  if (depth === 0) return { height: height && `${foldedCardHeight(notice)}px` }
  const hidden = depth > MAX_EDGES
  return {
    height: hidden ? 0 : `${EDGE}px`,
    marginInline: `${depth * EDGE}px`,
    opacity: hidden ? 0 : 1,
    transitionDelay: `${(MAX_EDGES - depth) * STAGGER}ms`,
  }
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
