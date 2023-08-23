<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="[{ label: title }]" />
    </template>
  </LayoutHeader>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Breadcrumbs from '@/components/Breadcrumbs.vue'
let title = 'Dashboard'
</script>
