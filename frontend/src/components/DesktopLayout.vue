<template>
  <div class="flex h-full">
    <div>
      <AppSidebar />
    </div>
    <div class="w-full">
      <slot />
    </div>
  </div>
</template>
<script setup>
import AppSidebar from './AppSidebar.vue'
</script>
