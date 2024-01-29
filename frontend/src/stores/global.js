import { useStorage } from '@vueuse/core'
import { defineStore } from 'pinia'
import { getCurrentInstance, ref } from 'vue'

export const globalStore = defineStore('crm-global', () => {
  const app = getCurrentInstance()
  const { $dialog } = app.appContext.config.globalProperties

  let twilioEnabled = ref(false)
  let isSidebarCollapsed = useStorage('isSidebarCollapsed', false)
  let callMethod = () => {}

  function setTwilioEnabled(value) {
    twilioEnabled.value = value
  }

  function setMakeCall(value) {
    callMethod = value
  }

  function makeCall(number) {
    callMethod(number)
  }

  function setIsSidebarCollapsed(value) {
    isSidebarCollapsed.value = value
  }

  return {
    $dialog,
    twilioEnabled,
    isSidebarCollapsed,
    setIsSidebarCollapsed,
    makeCall,
    setTwilioEnabled,
    setMakeCall,
  }
})
