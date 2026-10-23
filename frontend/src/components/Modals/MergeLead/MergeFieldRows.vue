<template>
  <div class="flex flex-col">
    <div
      v-for="field in conflicts"
      :key="field.fieldname"
      role="radiogroup"
      :aria-labelledby="`merge-field-${field.fieldname}`"
      class="grid grid-cols-[150px_minmax(0,1fr)_minmax(0,1fr)] items-center gap-2 border-b border-outline-gray-1 py-2 first:pt-0"
    >
      <span
        :id="`merge-field-${field.fieldname}`"
        class="flex min-w-0 items-center gap-1 text-base text-ink-gray-7"
      >
        <span class="truncate">{{ field.label }}</span>
        <span
          v-if="field.fieldname === 'website'"
          class="lucide-arrow-up-right size-3.5 shrink-0 text-ink-gray-5"
          aria-hidden="true"
        />
      </span>
      <Tooltip v-for="side in SIDES" :key="side" :text="displayOf(field, side)">
        <div
          role="radio"
          :aria-checked="picks[field.fieldname] === side"
          :tabindex="picks[field.fieldname] === side ? 0 : -1"
          :data-side="side"
          class="flex h-8 min-w-0 cursor-pointer items-center rounded border px-3 text-base focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
          :class="
            picks[field.fieldname] === side
              ? 'border-transparent bg-surface-gray-3 text-ink-gray-9'
              : 'border-outline-gray-2 bg-surface-white text-ink-gray-7 hover:bg-surface-gray-1'
          "
          @click="emit('pick', field.fieldname, side)"
          @keydown="onKeydown($event, field.fieldname, side)"
        >
          <span class="truncate">{{ displayOf(field, side) }}</span>
        </div>
      </Tooltip>
    </div>

    <div v-if="autoFields.length" :class="{ 'mt-3': conflicts.length }">
      <button
        type="button"
        class="flex items-center gap-1 rounded text-base text-ink-gray-6 hover:text-ink-gray-8 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
        :aria-expanded="showAuto"
        @click="showAuto = !showAuto"
      >
        <span
          class="lucide-chevron-right size-4 transition-transform duration-200"
          :class="{ 'rotate-90': showAuto }"
          aria-hidden="true"
        />
        {{
          autoFields.length === 1
            ? __('1 more field merged automatically')
            : __('{0} more fields merged automatically', [autoFields.length])
        }}
      </button>
      <dl
        v-if="showAuto"
        class="mt-2 grid grid-cols-[150px_minmax(0,1fr)] gap-x-2 gap-y-2 pl-5"
      >
        <template v-for="field in autoFields" :key="field.fieldname">
          <dt class="truncate text-base text-ink-gray-5">{{ field.label }}</dt>
          <dd class="min-w-0 text-base text-ink-gray-8">
            <Tooltip :text="pickedDisplay(field)">
              <span class="block truncate">{{ pickedDisplay(field) }}</span>
            </Tooltip>
          </dd>
        </template>
      </dl>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Tooltip } from 'frappe-ui'
import { nextTick, ref } from 'vue'
import type { MergeField, MergeSide } from '@/composables/useLeadMerge'

// target first: it is the lead being kept and the default pick
const SIDES: MergeSide[] = ['target', 'source']

defineProps<{
  conflicts: MergeField[]
  autoFields: MergeField[]
  picks: Record<string, MergeSide>
  displayOf: (field: MergeField, side: MergeSide) => string
  pickedDisplay: (field: MergeField) => string
}>()

const emit = defineEmits<{ pick: [fieldname: string, side: MergeSide] }>()

const showAuto = ref(false)

function onKeydown(e: KeyboardEvent, fieldname: string, side: MergeSide) {
  let next: MergeSide | null = null
  if (e.key === ' ' || e.key === 'Enter') next = side
  else if (['ArrowLeft', 'ArrowUp'].includes(e.key)) next = 'target'
  else if (['ArrowRight', 'ArrowDown'].includes(e.key)) next = 'source'
  if (!next) return
  e.preventDefault()
  emit('pick', fieldname, next)
  const group = (e.currentTarget as HTMLElement).closest('[role=radiogroup]')
  nextTick(() =>
    group?.querySelector<HTMLElement>(`[data-side=${next}]`)?.focus(),
  )
}
</script>
