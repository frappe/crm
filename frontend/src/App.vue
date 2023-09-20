<template>
  <router-view v-if="$route.name == 'Login'" />
  <DesktopLayout v-else-if="session().isLoggedIn">
    <router-view />
  </DesktopLayout>
  <Toasts />
</template>

<script setup>
import DesktopLayout from '@/components/DesktopLayout.vue'
import { sessionStore as session } from '@/stores/session'
import { Toasts } from 'frappe-ui'
</script>
