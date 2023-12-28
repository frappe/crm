import { defineStore } from 'pinia'
import { getCurrentInstance } from 'vue'

export const globalStore = defineStore('crm-global', () => {
  const app = getCurrentInstance()
  const { $dialog } = app.appContext.config.globalProperties

  return {
    $dialog,
  }
})
