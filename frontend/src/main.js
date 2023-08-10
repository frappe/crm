import './index.css'

import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import { createPinia } from 'pinia'

import { FrappeUI, Button, setConfig, frappeRequest } from 'frappe-ui'
import socket from './socket'
import { getCachedListResource } from 'frappe-ui/src/resources/listResource'
import { getCachedResource } from 'frappe-ui/src/resources/resources'

// create a pinia instance
let pinia = createPinia()

let app = createApp(App)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
app.use(router)

app.component('Button', Button)
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
