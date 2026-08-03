<template>
  <div class="crm-app-header flex pr-5">
    <div id="app-header" class="flex-1"></div>
    <div class="flex items-center justify-center">
      <CallUI />
    </div>
  </div>
</template>

<script setup>
import CallUI from '@/components/Telephony/CallUI.vue'
</script>

<style scoped>
.crm-app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: var(--glass-bg);
  -webkit-backdrop-filter: blur(12px) saturate(140%);
  backdrop-filter: blur(12px) saturate(140%);
  border-bottom: 1px solid var(--glass-border-color);
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .crm-app-header {
    background: var(--surface-gray-1);
  }
}
</style>
