<template>
  <div class="flex h-screen w-screen">
    <div class="h-full border-r bg-surface-gray-1">
      <AppSidebar />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto bg-surface-base">
      <AppHeader />
      <slot />
    </div>
    <GlobalModals />
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import GlobalModals from '@/components/Modals/GlobalModals.vue'
</script>
