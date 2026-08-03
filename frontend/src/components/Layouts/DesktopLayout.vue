<template>
  <div class="flex h-screen w-screen">
    <AppSidebar />
    <div class="crm-content-col flex-1 flex flex-col h-full overflow-auto bg-surface-base">
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

<style scoped>
/* Ambient red haze at top-left via ::before so bg-surface-base is not overridden */
.crm-content-col {
  position: relative;
  isolation: isolate;
}
.crm-content-col::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background: radial-gradient(
    55% 40% at 15% 0%,
    var(--brand-tint-07) 0%,
    transparent 60%
  );
}
/* Slot content and header sit above the haze */
.crm-content-col > * {
  position: relative;
  z-index: 1;
}
</style>
