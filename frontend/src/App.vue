<template>
  <router-view v-if="$route.name == 'Login'" />
  <Layout v-else-if="session().isLoggedIn">
    <router-view />
  </Layout>
  <Dialogs />
  <Toasts />
</template>

<script setup>
import { Dialogs } from '@/utils/dialogs'
import { sessionStore as session } from '@/stores/session'
import { useScreenSize } from '@/composables'
import { Toasts } from 'frappe-ui'
import { computed, defineAsyncComponent } from 'vue'

const screenSize = useScreenSize()
const MobileLayout = defineAsyncComponent(() =>
  import('./components/Layouts/MobileLayout.vue')
)
const DesktopLayout = defineAsyncComponent(() =>
  import('./components/Layouts/DesktopLayout.vue')
)
const Layout = computed(() => {
  if (screenSize.width < 640) {
    return MobileLayout
  } else {
    return DesktopLayout
  }
})
</script>
