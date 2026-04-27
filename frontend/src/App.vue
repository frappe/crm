<template>
  <FrappeUIProvider>
    <NotPermitted v-if="$route.name === 'Not Permitted'" />
    <Layout v-else-if="session.isLoggedIn" class="isolate">
      <router-view :key="$route.fullPath" />
    </Layout>
    <Dialogs />
<<<<<<< HEAD
<<<<<<< HEAD
=======
    <EventNotificationPopup />
    <DoctypeModal
      v-if="doctypeModal.show.value"
      v-model="doctypeModal.show.value"
      :doctypeTitle="doctypeModal.title.value"
      :doctype="doctypeModal.doctype.value"
      :docname="doctypeModal.name.value"
      :defaults="doctypeModal.defaults.value"
      @afterInsert="(d) => doctypeModal.triggerCallback('afterInsert', d)"
      @afterUpdate="(d) => doctypeModal.triggerCallback('afterUpdate', d)"
    />
>>>>>>> 0d5ca557 (feat: make doctypeModal composable a singleton with callback support)
=======
    <DoctypeModals />
    <EventNotificationPopup />
>>>>>>> 3d3d0a67 (refactor: replace DoctypeModal with DoctypeModals component for better modularity)
  </FrappeUIProvider>
</template>

<script setup>
import NotPermitted from '@/pages/NotPermitted.vue'
<<<<<<< HEAD
=======
import EventNotificationPopup from '@/components/EventNotificationPopup.vue'
<<<<<<< HEAD
import DoctypeModal from '@/components/Modals/DoctypeModal.vue'
>>>>>>> 0d5ca557 (feat: make doctypeModal composable a singleton with callback support)
=======
import DoctypeModals from '@/components/Modals/DoctypeModals.vue'
>>>>>>> 3d3d0a67 (refactor: replace DoctypeModal with DoctypeModals component for better modularity)
import { Dialogs } from '@/utils/dialogs'
import { sessionStore } from '@/stores/session'
import { FrappeUIProvider, setConfig, useTheme } from 'frappe-ui'
import { computed, defineAsyncComponent, provide } from 'vue'

const session = sessionStore()
provide('session', session)

const { setTheme } = useTheme()
if (!localStorage.getItem('theme')) {
  setTheme('light')
}

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
