<template>
  <div class="flex h-screen w-screen">
    <div class="h-full border-r bg-gray-50 w-[220px]">
      <AppSidebar />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto">
      <slot />
    </div>
  </div>
</template>
<script setup>
import AppSidebar from '@/components/AppSidebar.vue'
</script>
