<template>
  <router-view v-if="$route.name == 'Login'" />
  <CallUI v-else-if="$session.isLoggedIn">
    <DesktopLayout>
      <router-view />
    </DesktopLayout>
  </CallUI>
  <Toasts />
</template>

<script setup>
import DesktopLayout from '@/components/DesktopLayout.vue'
import CallUI from './components/CallUI.vue'
import { Toasts } from 'frappe-ui'
</script>
