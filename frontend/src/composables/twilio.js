import { getCurrentInstance } from 'vue'

export function is_twilio_enabled() {
  const app = getCurrentInstance()
  return app.appContext.config.globalProperties.is_twilio_enabled
}
