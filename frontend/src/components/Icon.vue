<template>
  <div v-if="isEmoji(icon)" v-bind="$attrs">
    {{ icon }}
  </div>
  <!-- lucide icon from the sprite the IconPicker reads (lucide is a superset of
       feather, so legacy names still resolve). No width/height attrs so size
       classes like `h-4` control it. -->
  <svg
    v-else-if="typeof icon == 'string'"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.5"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="shrink-0"
    v-bind="$attrs"
  >
    <use :href="`#${spriteName(icon)}`" />
  </svg>
  <component :is="icon" v-else v-bind="$attrs" />
</template>
<script setup>
import { isEmoji } from '@/utils'

defineProps({ icon: { type: [String, Object], required: true } })

function spriteName(icon) {
  const name = icon.replace(/^lucide-/, '')
  return RENAMED_FEATHER_ICONS[name] ?? name
}

// The sprite has only current lucide names; saved Form Scripts may still use these old feather names
const RENAMED_FEATHER_ICONS = {
  'alert-circle': 'circle-alert',
  'alert-octagon': 'octagon-alert',
  'alert-triangle': 'triangle-alert',
  'align-center': 'text-align-center',
  'align-justify': 'text-align-justify',
  'align-left': 'text-align-start',
  'align-right': 'text-align-end',
  'arrow-down-circle': 'circle-arrow-down',
  'arrow-left-circle': 'circle-arrow-left',
  'arrow-right-circle': 'circle-arrow-right',
  'arrow-up-circle': 'circle-arrow-up',
  'bar-chart-2': 'chart-no-axes-column',
  'bar-chart': 'chart-no-axes-column-increasing',
  'check-circle': 'circle-check-big',
  'check-square': 'square-check-big',
  columns: 'columns-2',
  'divide-circle': 'circle-divide',
  'divide-square': 'square-divide',
  'download-cloud': 'cloud-download',
  'edit-2': 'pen',
  'edit-3': 'pen-line',
  edit: 'square-pen',
  filter: 'funnel',
  frown: 'face-slightly-frowning',
  'git-commit': 'git-commit-horizontal',
  grid: 'grid-3x3',
  'help-circle': 'circle-question-mark',
  home: 'house',
  layout: 'panels-top-left',
  meh: 'face-neutral',
  'minus-circle': 'circle-minus',
  'minus-square': 'square-minus',
  'more-horizontal': 'ellipsis',
  'more-vertical': 'ellipsis-vertical',
  'pause-circle': 'circle-pause',
  'pie-chart': 'chart-pie',
  'play-circle': 'circle-play',
  'plus-circle': 'circle-plus',
  'plus-square': 'square-plus',
  sidebar: 'panel-left',
  sliders: 'sliders-vertical',
  smile: 'face-slightly-smiling',
  'stop-circle': 'circle-stop',
  'trash-2': 'trash',
  unlock: 'lock-open',
  'upload-cloud': 'cloud-upload',
  'x-circle': 'circle-x',
  'x-octagon': 'octagon-x',
  'x-square': 'square-x',
}
</script>
