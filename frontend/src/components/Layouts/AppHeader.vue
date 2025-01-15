<template>
  <div class="flex border-b pr-5">
    <div id="app-header" class="flex-1"></div>
    <div class="flex items-center justify-center">
      <ExotelCallUI />
      <CallUI />
    </div>
  </div>
</template>

<script setup>
import ExotelCallUI from '@/components/Telephony/ExotelCallUI.vue'
import CallUI from '@/components/Telephony/CallUI.vue'
</script>
