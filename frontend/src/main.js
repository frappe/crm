import './index.css'
// Import custom scrollbar styles for dark theme
import './styles/scrollbar.css'
// Import dark mode styles
import './styles/dark-mode.css'
import './utils/dayjs'

import { createApp, watch } from 'vue'
import { createPinia } from 'pinia'
import { createDialog } from './utils/dialogs'
import { initSocket } from './socket'
import router from './router'
import translationPlugin, { translationsReady, __ } from './translation'
import { posthogPlugin } from './telemetry'
import App from './App.vue'
import { setLocale } from './utils/translation'

import {
  FrappeUI,
  Button,
  Input,
  TextInput,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  setConfig,
  frappeRequest,
  FeatherIcon,
} from 'frappe-ui'

let globalComponents = {
  Button,
  TextInput,
  Input,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
  FeatherIcon,
}

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
app.use(translationPlugin)

// Make __ available globally
window.__ = __

async function initApp() {
  // Wait for translations to be ready before initializing router
  await new Promise(resolve => {
    if (translationsReady.value) {
      resolve();
    } else {
      const unwatch = watch(translationsReady, (ready) => {
        if (ready) {
          unwatch();
          resolve();
        }
      });
    }
  });

  // Initialize locale after translations are ready
  const locale = window.frappe?.boot?.lang || window.navigator.language || 'en'
  await setLocale(locale)

  app.use(router)
  app.use(posthogPlugin)
  for (let key in globalComponents) {
    app.component(key, globalComponents[key])
  }

  app.config.globalProperties.$dialog = createDialog

  let socket
  if (import.meta.env.DEV) {
    frappeRequest({ url: '/api/method/crm.www.crm.get_context_for_dev' }).then(
      (values) => {
        for (let key in values) {
          window[key] = values[key]
        }
        socket = initSocket()
        app.config.globalProperties.$socket = socket
        app.mount('#app')
      },
    )
  } else {
    socket = initSocket()
    app.config.globalProperties.$socket = socket
    app.mount('#app')
  }

  if (import.meta.env.DEV) {
    window.$dialog = createDialog
  }
}

initApp();
