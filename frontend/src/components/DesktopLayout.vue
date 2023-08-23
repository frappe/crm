<template>
  <div class="flex h-screen w-screen">
    <div class="h-full border-r bg-gray-50 w-[220px]">
      <AppSidebar />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto">
      <div id="app-header" class="flex">
        <div id="header-area" class="flex-1"></div>
        <div id="call-area" class="flex items-center justify-center"></div>
      </div>
      <slot />
    </div>
  </div>
</template>
<script setup>
import AppSidebar from '@/components/AppSidebar.vue'
</script>
