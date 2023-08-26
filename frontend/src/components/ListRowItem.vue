<template>
  <Tooltip
    :text="tooltipText"
    :html="tooltipHTML"
    class="flex items-center space-x-2.5"
  >
    <slot name="prefix"></slot>
    <div class="text-base truncate">
      {{ label }}
    </div>
  </Tooltip>
</template>
<script setup>
import { dateFormat, timeAgo, dateTooltipFormat, htmlToText } from '@/utils'
import { Tooltip } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'text',
  },
  value: {
    type: [String, Number, Object],
    default: '',
  },
})

const tooltipHTML = computed(() => {
  if (props.type === 'html') {
    return props.value?.toString()
  }
  return ''
})

const tooltipText = computed(() => {
  if (props.type === 'html') return ''
  if (props.type === 'pretty_date') {
    return dateFormat(props.value, dateTooltipFormat)
  }
  return props.value?.toString()
})

const label = computed(() => {
  if (props.type === 'pretty_date') {
    return timeAgo(props.value)
  }
  if (props.type === 'html') {
    return htmlToText(props.value?.toString())
  }
  return props.value?.toString()
})
</script>
