<template>
  <Teleport to="#app-header" v-if="showHeader">
    <header class="flex justify-between items-center pl-5 py-2.5 h-12">
      <div class="flex items-center gap-2">
        <slot name="left-header" />
      </div>
      <div class="flex items-center gap-2">
        <slot name="right-header" class="flex items-center gap-2" />
      </div>
    </header>
  </Teleport>
</template>
<script setup>
import { ref, nextTick } from 'vue'

const showHeader = ref(false)

nextTick(() => {
  showHeader.value = true
})
</script>
