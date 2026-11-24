<template>
  <FrappeUIProvider>
    <NotPermitted v-if="$route.name === 'Not Permitted'" />
    <router-view v-else-if="$route.name === 'Setup'" />
    <!-- no shell until the first route resolves, which may be the setup -->
    <Layout v-else-if="session.isLoggedIn && $route.name" class="isolate">
      <router-view
        :key="$route.meta.viewKey || $route.fullPath.split('#')[0]"
      />
    </Layout>
    <Dialogs />
    <DoctypeModals />
    <EventNotificationPopup />
  </FrappeUIProvider>
</template>

<script setup>
import NotPermitted from '@/pages/NotPermitted.vue'
import EventNotificationPopup from '@/components/EventNotificationPopup.vue'
import DoctypeModals from '@/components/Modals/DoctypeModals.vue'
import { Dialogs } from '@/utils/dialogs'
import { sessionStore } from '@/stores/session'
import { FrappeUIProvider, setConfig, useColorScheme } from 'frappe-ui'
import { layoutFor } from '@/components/Layouts/layouts'
import { computed, provide } from 'vue'

const session = sessionStore()
provide('session', session)

const { setColorScheme } = useColorScheme()
if (!localStorage.getItem('theme')) {
  setColorScheme('light')
}

const Layout = computed(() => layoutFor(window.innerWidth))

setConfig('systemTimezone', window.timezone?.system || null)
setConfig('localTimezone', window.timezone?.user || null)
setConfig('translatedMessages', window.translated_messages || {})
</script>
