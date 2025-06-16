<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <SpancoWidget />
<!--  <Calender />-->
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs } from 'frappe-ui'
import SpancoWidget from '@/components/Dashboard Elements/SpancoWidget.vue'
let title = 'Dashboard'
const breadcrumbs = [{ label: title, route: { name: 'Dashboard' } }]
</script>
