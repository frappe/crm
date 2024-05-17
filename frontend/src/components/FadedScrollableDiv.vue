<template>
  <div ref="scrollableDiv" class="scrr" :style="`maskImage: ${maskStyle}`">
    <slot></slot>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  maskHeight: {
    type: Number,
    default: 20,
  },
})

const scrollableDiv = ref(null)
const maskStyle = ref('none')

function setMaskStyle() {
  // show mask only if div is scrollable
  if (scrollableDiv.value.scrollHeight > scrollableDiv.value.clientHeight) {
    maskStyle.value = `linear-gradient(to bottom, black calc(100% - ${props.maskHeight}px), transparent 100%);`
  } else {
    maskStyle.value = 'none'
  }
}

onMounted(() => setMaskStyle())
</script>
