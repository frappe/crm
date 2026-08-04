<template>
  <Tooltip :text="tooltipText">
    <div :class="className">{{ displayText }}</div>
  </Tooltip>
</template>

<script setup>
import { Tooltip } from 'frappe-ui'
import { timeAgo, formatDate } from '@/utils'
import { useTimelinePreferences } from '@/composables/useTimelinePreferences'
import { computed } from 'vue'

const props = defineProps({
  date: { type: [String, Object], default: '' },
  // Format used for the exact timestamp (falls back to the default in formatDate)
  format: { type: String, default: '' },
  className: { type: String, default: 'text-sm text-ink-gray-5' },
})

const { showExactTimestamp } = useTimelinePreferences()

const relative = computed(() => __(timeAgo(props.date)))
const exact = computed(() => formatDate(props.date, props.format || undefined))

const displayText = computed(() =>
  showExactTimestamp.value ? exact.value : relative.value,
)
const tooltipText = computed(() =>
  showExactTimestamp.value ? relative.value : exact.value,
)
</script>
