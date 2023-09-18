import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import { createPinia } from 'pinia'

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
} from 'frappe-ui'
import socket from './socket'
import { sessionStore as session } from './stores/session'
import { usersStore } from './stores/users'
import { getCachedListResource } from 'frappe-ui/src/resources/listResource'
import { getCachedResource } from 'frappe-ui/src/resources/resources'

let globalComponents = {
  Button,
  TextInput,
  Input,
  FormControl,
  ErrorMessage,
  Dialog,
  Alert,
  Badge,
}

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
app.use(router)
for (let key in globalComponents) {
  app.component(key, globalComponents[key])
}

let { getUser, users } = usersStore()

app.config.globalProperties.$user = getUser
app.config.globalProperties.$users = users
app.config.globalProperties.$session = session()

app.mount('#app')

socket.on('refetch_resource', (data) => {
  if (data.cache_key) {
    let resource =
      getCachedResource(data.cache_key) || getCachedListResource(data.cache_key)
    if (resource) {
      resource.reload()
    }
  }
})

if (import.meta.env.DEV) {
  window.$user = getUser
  window.$users = users
  window.$session = session()
}
