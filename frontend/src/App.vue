<template>
  <FrappeUIProvider>
    <NotPermitted v-if="$route.name === 'Not Permitted'" />
    <Layout v-else-if="session.isLoggedIn" class="isolate">
      <router-view :key="$route.fullPath" />
    </Layout>
    <Dialogs />
  </FrappeUIProvider>
</template>

<script setup>
import NotPermitted from '@/pages/NotPermitted.vue'
import { Dialogs } from '@/utils/dialogs'
import { sessionStore } from '@/stores/session'
import { FrappeUIProvider, setConfig } from 'frappe-ui'
import { computed, defineAsyncComponent, provide } from 'vue'

const session = sessionStore()
provide('session', session)

const MobileLayout = defineAsyncComponent(
  () => import('./components/Layouts/MobileLayout.vue'),
)
const DesktopLayout = defineAsyncComponent(
  () => import('./components/Layouts/DesktopLayout.vue'),
)
const Layout = computed(() => {
  if (window.innerWidth < 640) {
    return MobileLayout
  } else {
    return DesktopLayout
  }
})

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
setConfig('translatedMessages', window.translated_messages || {})
</script>
