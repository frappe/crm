import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  FrappeUI,
  Button,
  setConfig,
  frappeRequest,
} from 'frappe-ui'

import FinanceCockpit from './pages/FinanceCockpit/index.vue'

const pinia = createPinia()
const app = createApp(FinanceCockpit)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)

// Boot data is injected by Jinja in production; in dev it's fetched by the page
if (import.meta.env.DEV) {
  frappeRequest({ url: '/api/method/crm.www.crm.get_context_for_dev' }).then(
    (values) => {
      for (let key in values) {
        window[key] = values[key]
      }
      app.mount('#finance-cockpit-root')
    },
  )
} else {
  app.mount('#finance-cockpit-root')
}
