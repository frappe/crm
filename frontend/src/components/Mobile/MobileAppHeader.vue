<template>
  <div class="flex pr-3">
    <div class="z-20 ml-2 flex items-center justify-center">
      <Button
        class="size-7"
        variant="ghosted"
        @click="sidebarOpened = !sidebarOpened"
      >
        <MenuIcon class="h-4" />
      </Button>
    </div>
    <div id="app-header" class="flex-1" />
  </div>
  <CallUI class="mr-3 mt-2" />
</template>

<script setup>
import MenuIcon from '@/components/Icons/MenuIcon.vue'
import CallUI from '@/components/CallUI.vue'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
</script>
