<template>
  <slot v-bind="{ opened, open, close, toggle }"></slot>
</template>
<script setup>
import { ref } from 'vue'
const props = defineProps({
  isOpened: {
    type: Boolean,
    default: true,
  },
})
function toggle() {
  opened.value = !opened.value
}

function open() {
  opened.value = true
}

function close() {
  opened.value = false
}
let opened = ref(props.isOpened)
</script>
