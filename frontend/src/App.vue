<template>
  <router-view v-if="$route.name == 'Login'" />
  <DesktopLayout v-else-if="session().isLoggedIn">
    <router-view />
  </DesktopLayout>
  <Dialogs />
  <Toasts />
</template>

<script setup>
import DesktopLayout from '@/components/Layouts/DesktopLayout.vue'
import { Dialogs } from '@/utils/dialogs'
import { sessionStore as session } from '@/stores/session'
import { Toasts } from 'frappe-ui'
</script>
