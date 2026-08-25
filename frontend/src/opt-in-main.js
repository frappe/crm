import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { FrappeUI, setConfig, frappeRequest } from 'frappe-ui'

import OptInWizard from './pages/OptIn/OptInWizard.vue'
import translationPlugin from './translation'

const el = document.getElementById('optin-app')
const networkSlug = (el && el.dataset.network) ? el.dataset.network : ''

const pinia = createPinia()
const app = createApp(OptInWizard, { networkSlug })

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
app.use(translationPlugin)

app.mount(el || '#optin-app')
