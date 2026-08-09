<template>
  <section
    class="fc-section-card rounded-xl border bg-surface-white shadow-sm transition-colors"
    :class="hero ? toneCls.heroBorder : 'border-outline-gray-1'"
  >
    <header
      class="flex items-center justify-between gap-3 px-4 sm:px-5 py-3 border-b border-outline-gray-1"
      :class="collapsible ? 'cursor-pointer select-none' : ''"
      @click="collapsible && toggle()"
    >
      <div class="flex items-center gap-2.5 min-w-0">
        <span
          class="flex items-center justify-center w-7 h-7 rounded-lg"
          :class="toneCls.chip"
        >
          <FcIcon :name="icon" :size="16" />
        </span>
        <h3 class="text-sm font-semibold text-ink-gray-8 truncate">{{ title }}</h3>
        <span v-if="badge" class="text-xs font-medium text-ink-gray-4">{{ badge }}</span>
      </div>
      <div class="flex items-center gap-2">
        <slot name="header-action" />
        <button
          v-if="collapsible"
          type="button"
          class="text-ink-gray-4 transition-transform"
          :class="isOpen ? 'rotate-180' : ''"
          :aria-label="isOpen ? 'Collapse' : 'Expand'"
          @click.stop="toggle"
        >
          <FcIcon name="chevron-down" :size="18" />
        </button>
      </div>
    </header>

    <div v-show="isOpen" class="px-4 sm:px-5 py-4">
      <slot />
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import FcIcon from './FcIcon.vue'

const props = defineProps({
  title: { type: String, required: true },
  icon: { type: String, default: 'file-text' },
  hero: { type: Boolean, default: false },
  collapsible: { type: Boolean, default: false },
  collapsed: { type: Boolean, default: false },
  badge: { type: [String, Number], default: '' },
  // Semantic tone for the header icon chip — lets a form's sections read as
  // colour-coded zones (party=neutral, items=positive, taxes=pending, totals=neutral).
  // NOTE: this fork rebrands `blue` -> Tiberbu red, so there is no `info`/blue tone;
  // neutral (gray) is the calm default. Chips pair a pale surface-*-2 fill with a
  // dark, legible ink-*-6 glyph — verified for contrast in BOTH light and dark.
  tone: { type: String, default: 'neutral' },
})

const TONES = {
  neutral:   { chip: 'bg-surface-gray-3 text-ink-gray-7',    heroBorder: 'border-outline-gray-3' },
  positive:  { chip: 'bg-surface-green-2 text-ink-green-6',  heroBorder: 'border-outline-green-1' },
  attention: { chip: 'bg-surface-red-2 text-ink-red-6',      heroBorder: 'border-outline-red-1' },
  pending:   { chip: 'bg-surface-amber-2 text-ink-amber-6',  heroBorder: 'border-outline-amber-1' },
}
const toneCls = computed(() => TONES[props.tone] || TONES.neutral)

const isOpen = ref(!(props.collapsible && props.collapsed))
function toggle() { isOpen.value = !isOpen.value }
</script>
