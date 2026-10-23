<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Home" />
      </template>
    </LayoutHeader>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { getSettings } from '@/stores/settings'
import { usePageMeta } from 'frappe-ui'

const { brand } = getSettings()

usePageMeta(() => ({ title: __('Home'), icon: brand.favicon }))
</script>
