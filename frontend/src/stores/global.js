import { defineStore } from 'pinia'
import { getCurrentInstance, ref } from 'vue'

export const globalStore = defineStore('crm-global', () => {
  const app = getCurrentInstance()
  const { $dialog, $socket } = app.appContext.config.globalProperties

  let callMethod = (number) => {
    console.log(`Default call method called with number: ${number}`);
    
    nativeInterface.execute('dialCall', number)
  }

  function setMakeCall(value) {
    callMethod = value
  }

  function makeCall(number) {
    callMethod(number)
  }

  return {
    $dialog,
    $socket,
    makeCall,
    setMakeCall,
  }
})
