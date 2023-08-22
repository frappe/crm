<template>
  <router-view v-if="$route.name == 'Login'" />
  <CallUI v-else-if="session().isLoggedIn">
    <DesktopLayout>
      <router-view />
    </DesktopLayout>
  </CallUI>
</template>

<script setup>
import DesktopLayout from '@/components/DesktopLayout.vue'
import { sessionStore as session } from '@/stores/session'
import CallUI from './components/CallUI.vue'
</script>
