import '../../index.css'

import { createApp } from 'vue'
import { FrappeUI, setConfig, frappeRequest } from 'frappe-ui'

import SigningApp from './SigningApp.vue'
import translationPlugin from '../../translation'

const el = document.getElementById('signing-app')

const app = createApp(SigningApp)

setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(translationPlugin)

app.mount(el || '#signing-app')
