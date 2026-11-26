<template>
  <div>
    <img
      v-if="brand?.logo"
      :src="brand.logo"
      class="h-full w-auto max-w-full object-contain"
    />
    <CRMLogo v-else class="h-full w-auto rounded-4" />
  </div>
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'

const brand = defineModel({ type: Object, default: () => ({}) })
</script>
