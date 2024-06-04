<template>
  <div class="flex border-b pr-3">
    <div class="z-20 -mr-4 ml-1 flex items-center justify-center">
      <Button variant="ghosted" @click="sidebarOpened = !sidebarOpened">
        <FeatherIcon name="menu" class="size-4" />
      </Button>
    </div>
    <div id="app-header" class="flex-1" />
  </div>
  <CallUI class="mr-3 mt-2" />
</template>

<script setup>
import CallUI from '@/components/CallUI.vue'
import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
</script>
