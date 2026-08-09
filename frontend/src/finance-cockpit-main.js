import './index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import {
  FrappeUI,
  setConfig,
  frappeRequest,
} from 'frappe-ui'

import FinanceCockpit from './pages/FinanceCockpit/index.vue'
import translationPlugin from './translation'

const pinia = createPinia()
const app = createApp(FinanceCockpit)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(pinia)
// Installs window.__ / global __ — ported CRM components (e.g. ThemeSwitcher)
// call __() in their templates and render nothing if it is undefined.
app.use(translationPlugin)

// Production: boot data injected by Jinja in finance-cockpit.html (www page)
// Dev: fetch from the www context endpoint
if (import.meta.env.DEV) {
  frappeRequest({ url: '/api/method/crm.www.finance_cockpit.get_context_for_dev' }).then(
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
