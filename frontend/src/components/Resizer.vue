<template>
  <div class="relative" :style="{ width: `${sidebarWidth}px` }">
    <slot v-bind="{ sidebarResizing, sidebarWidth }" />
    <div
      class="absolute left-0 z-10 h-full w-1 cursor-col-resize bg-gray-300 opacity-0 transition-opacity hover:opacity-100"
      :class="{ 'opacity-100': sidebarResizing }"
      @mousedown="startResize"
    />
  </div>
</template>
<script setup>
import { ref } from 'vue'

const props = defineProps({
  defaultWidth: {
    type: Number,
    default: 352,
  },
  minWidth: {
    type: Number,
    default: 16 * 16,
  },
  maxWidth: {
    type: Number,
    default: 30 * 16,
  },
  side: {
    type: String,
    default: 'left',
  },
})

const sidebarResizing = ref(false)
const sidebarWidth = ref(props.defaultWidth)

function startResize() {
  document.addEventListener('mousemove', resize)
  document.addEventListener('mouseup', () => {
    document.body.classList.remove('select-none')
    document.body.classList.remove('cursor-col-resize')
    localStorage.setItem('sidebarWidth', sidebarWidth.value)
    sidebarResizing.value = false
    document.removeEventListener('mousemove', resize)
  })
}
function resize(e) {
  sidebarResizing.value = true
  document.body.classList.add('select-none')
  document.body.classList.add('cursor-col-resize')
  sidebarWidth.value =
    props.side == 'left' ? e.clientX : window.innerWidth - e.clientX

  // snap to props.defaultWidth
  let range = [props.defaultWidth - 10, props.defaultWidth + 10]
  if (sidebarWidth.value > range[0] && sidebarWidth.value < range[1]) {
    sidebarWidth.value = props.defaultWidth
  }

  if (sidebarWidth.value < props.minWidth) {
    sidebarWidth.value = props.minWidth
  }
  if (sidebarWidth.value > props.maxWidth) {
    sidebarWidth.value = props.maxWidth
  }
}
</script>
