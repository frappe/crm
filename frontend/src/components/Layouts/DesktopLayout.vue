<template>
  <div class="flex h-screen w-screen">
<<<<<<< HEAD
<<<<<<< HEAD
    <div class="h-full border-r bg-surface-menu-bar">
=======
    <div class="h-full border-r bg-surface-gray-1">
>>>>>>> 98b0a04a (fix: use bg-surface-gray-1 for desktop sidebar background)
=======
    <div class="h-full border-r bg-surface-sidebar">
>>>>>>> d9a84e70 (fix: use consistent bg-surface-sidebar token for desktop sidebar)
      <AppSidebar />
    </div>
    <div class="flex-1 flex flex-col h-full overflow-auto bg-surface-white">
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
