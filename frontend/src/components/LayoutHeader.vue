<template>
  <Teleport to="#app-header" v-if="showHeader">
    <slot>
      <header class="flex h-10.5 items-center justify-between py-[7px] sm:pl-5 pl-2">
        <div class="flex items-center gap-2">
          <slot name="left-header" />
        </div>
        <div class="flex items-center gap-2">
          <slot name="right-header" class="flex items-center gap-2" />
        </div>
      </header>
    </slot>
  </Teleport>
</template>
<script setup>
import { ref, nextTick } from 'vue'

const showHeader = ref(false)

nextTick(() => {
  showHeader.value = true
})
</script>
