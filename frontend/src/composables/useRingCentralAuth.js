// src/composables/useRingCentralAuth.js
import { ref } from 'vue'
import { createResource, call } from 'frappe-ui'

export function useRingCentralAuth() {
  const isRingCentralAuthorized = ref(false)
  const authorizationInProgress = ref(false)
  const log = ref('')

  const getAuthorizeUrl = createResource({
    url: 'crm.integrations.ringcentral.api.get_authorize_url',
    onSuccess(data) {
      authorizationInProgress.value = true
      window.open(data.authorize_url, '_blank')
    },
    onError(error) {
      log.value = `Failed to get authorization URL: ${error}`
      console.error(error)
    },
  })

  const checkAuthStatus = createResource({
    url: 'crm.integrations.ringcentral.api.check_auth_status',
    onSuccess(data) {
      isRingCentralAuthorized.value = data.is_authorized
      authorizationInProgress.value = false
    },
    onError(error) {
      log.value = `Failed to check auth status: ${error}`
      console.error(error)
    },
  })

  async function startOAuthFlow() {
    log.value = 'Starting OAuth flow...'
    authorizationInProgress.value = true
    getAuthorizeUrl.fetch()
  }

  function handleOAuthCallback(event) {
    if (event.origin !== window.location.origin) return
    if (event.data === 'OAuth flow completed. You can close this window.') {
      log.value = 'OAuth callback received, checking authentication...'
      checkAuthStatus.fetch()
    }
  }

  return {
    isRingCentralAuthorized,
    authorizationInProgress,
    log,
    startOAuthFlow,
    handleOAuthCallback,
    checkAuthStatus,
  }
}