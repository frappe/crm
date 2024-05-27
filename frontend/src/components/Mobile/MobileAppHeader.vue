<template>
  <div class="flex border-b pr-5">
    <div
      v-if="isMobileView"
      class="z-20 -mr-4 ml-2 flex items-center justify-center"
    >
      <Button variant="ghosted" @click="sidebarOpened = !sidebarOpened">
        <FeatherIcon name="menu" class="size-4" />
      </Button>
    </div>
    <div id="app-header" class="flex-1"></div>
    <div class="flex items-center justify-center">
      <CallUI />
    </div>
  </div>
</template>

<script setup>
import CallUI from '@/components/CallUI.vue'
import { useScreenSize } from '@/composables'
import { Button, FeatherIcon } from 'frappe-ui'
import { computed } from 'vue'
import { mobileSidebarOpened as sidebarOpened } from '@/stores/settings'

const screenSize = useScreenSize()
const isMobileView = computed(() => screenSize.width < 640)
</script>
