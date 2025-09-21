<template>
  <Tooltip v-if="!disabled">
    <template #body>
      <div
        class="rounded bg-surface-gray-7 py-1.5 px-2 text-xs text-ink-white shadow-xl"
      >
        <span class="flex items-center gap-1">
          <span>{{ label }}</span>
          <!-- Primary combos (one or many) -->
          <template
            v-for="(combo, idx) in primaryCombosDisplay"
            :key="'prim-' + idx + combo"
          >
            <KeyboardShortcut
              bg
              class="!bg-surface-gray-5 !text-ink-gray-2 px-1"
              :combo="combo"
            />
          </template>
          <!-- Alternate combos / equivalents -->
          <template
            v-for="(alt, idx) in altCombosDisplay"
            :key="'alt-' + idx + alt"
          >
            <KeyboardShortcut
              bg
              class="!bg-surface-gray-5 !text-ink-gray-2 px-1"
              :combo="alt"
            />
          </template>
        </span>
      </div>
    </template>
    <slot />
  </Tooltip>
  <slot v-else />
</template>

<script setup lang="ts">
import { Tooltip, KeyboardShortcut } from 'frappe-ui'
import { computed } from 'vue'

interface Props {
  label: string
  combo?: string | string[]
  altCombos?: string[]
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  combo: '',
  altCombos: () => [],
  disabled: false,
})

const isMac = computed(() => {
  if (typeof navigator === 'undefined') return false
  const platform =
    (navigator as any).userAgentData?.platform || navigator.platform || ''
  if (/Mac|iPod|iPhone|iPad/i.test(platform)) return true
  return /Mac OS X|Macintosh|iPhone|iPad|iPod/i.test(navigator.userAgent || '')
})

function normalizeCombo(raw: string): string {
  if (!raw) return ''
  if (/^mod\+/i.test(raw)) {
    const rest = raw.split('+').slice(1).join('+')
    return (isMac.value ? 'Cmd' : 'Ctrl') + '+' + rest
  }
  return raw
}

function normalizeList(list: string | string[]): string[] {
  const arr = Array.isArray(list) ? list : list ? [list] : []
  return arr.map(normalizeCombo)
}

// Dedupe Backspace/Delete (prefer Backspace) on macOS
function dedupeMacDeleteVariants(primary: string[], alts: string[]) {
  if (!isMac.value) return { primary, alts }
  const all = [...primary, ...alts]
  if (all.includes('Delete') && all.includes('Backspace')) {
    return {
      primary: primary.filter((k) => k !== 'Delete'),
      alts: alts.filter((k) => k !== 'Delete'),
    }
  }
  return { primary, alts }
}

// Base normalized lists
const normalizedPrimary = computed(() => normalizeList(props.combo))
const normalizedAlt = computed(() => props.altCombos.map(normalizeCombo))

// Apply dedupe once to both arrays to avoid circular dependency
const deduped = computed(() =>
  dedupeMacDeleteVariants(normalizedPrimary.value, normalizedAlt.value),
)

const primaryCombosDisplay = computed(() => deduped.value.primary)
const altCombosDisplay = computed(() => deduped.value.alts)

defineOptions({ name: 'ShortcutTooltip' })
</script>
