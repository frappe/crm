<template>
  <FrappeUIProvider>
    <Layout v-if="session().isLoggedIn">
      <router-view />
    </Layout>
    <Dialogs />
  </FrappeUIProvider>
</template>

<script setup>
import { Dialogs } from '@/utils/dialogs'
import { sessionStore as session } from '@/stores/session'
import { setTheme } from '@/stores/theme'
import { FrappeUIProvider, setConfig } from 'frappe-ui'
import { computed, defineAsyncComponent, onMounted } from 'vue'

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

onMounted(() => setTheme())

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
</script>
