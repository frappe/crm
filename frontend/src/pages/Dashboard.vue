<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>
  <SpancoWidget />
<!--  <Calender />-->
  <todo />
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs } from 'frappe-ui'
import SpancoWidget from '@/components/Dashboard Elements/SpancoWidget.vue'
import Todo from '@/components/Dashboard Elements/todo.vue'
let title = 'Dashboard'
const breadcrumbs = [{ label: title, route: { name: 'Dashboard' } }]
</script>
