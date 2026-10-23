<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Home" />
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-y-auto">
      <HomeHeader />
    </div>
  </div>
</template>

<script setup>
import HomeHeader from '@/components/Home/HomeHeader.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { getSettings } from '@/stores/settings'
import { usePageMeta } from 'frappe-ui'

const { brand } = getSettings()

usePageMeta(() => ({ title: __('Home'), icon: brand.favicon }))
</script>
