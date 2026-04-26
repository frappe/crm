<template>
  <FrappeUIProvider>
    <NotPermitted v-if="$route.name === 'Not Permitted'" />
    <Layout v-else-if="session.isLoggedIn" class="isolate">
      <router-view :key="$route.fullPath" />
    </Layout>
    <Dialogs />
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
  </FrappeUIProvider>
</template>

<script setup>
import NotPermitted from '@/pages/NotPermitted.vue'
import EventNotificationPopup from '@/components/EventNotificationPopup.vue'
import DoctypeModal from '@/components/Modals/DoctypeModal.vue'
import { Dialogs } from '@/utils/dialogs'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { sessionStore } from '@/stores/session'
import { FrappeUIProvider, setConfig, useTheme } from 'frappe-ui'
import { computed, defineAsyncComponent, provide } from 'vue'

const doctypeModal = useDoctypeModal()

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
