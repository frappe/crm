<template>
  <div class="flex h-screen w-screen">
    <div class="h-full border-r bg-gray-50">
      <AppSidebar />
    </div>
    <Notifications />
    <div class="flex-1 flex flex-col h-full overflow-auto">
      <AppHeader />
      <slot />
    </div>
  </div>
</template>
<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import Notifications from '@/components/Notifications.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
</script>
