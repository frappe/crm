<template>
  <div class="flex pe-3">
    <div class="z-20 ms-2 flex items-center justify-center">
      <Button
        class="size-7"
        variant="ghost"
        @click="sidebarOpened = !sidebarOpened"
      >
        <MenuIcon class="h-4 text-ink-gray-9" />
      </Button>
    </div>
    <div id="app-header" class="flex-1" />
  </div>
  <CallUI class="me-3 mt-2" />
</template>

<script setup>
import MenuIcon from '@/components/Icons/MenuIcon.vue'
import CallUI from '@/components/Telephony/CallUI.vue'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
</script>
