<template>
  <div v-if="brand?.logo">
    <img :src="brand.logo" class="h-full w-full object-cover" />
  </div>
  <CRMLogo v-else class="size-8 shrink-0 rounded" />
</template>

<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'

const brand = defineModel()
</script>
