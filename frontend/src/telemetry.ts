import '../../../frappe/frappe/public/js/lib/posthog.js'
import { createResource } from 'frappe-ui'
import { computed } from 'vue'

declare global {
  interface Window {
    posthog: any
  }
}
type PosthogSettings = {
  posthog_project_id: string
  posthog_host: string
  enable_telemetry: boolean
  telemetry_site_age: number
}
interface CaptureOptions {
  data: {
    user: string
    [key: string]: string | number | boolean | object
  }
}

let posthog: typeof window.posthog = window.posthog

// Posthog Settings
let posthogSettings = createResource({
  url: 'crm.api.get_posthog_settings',
  cache: 'posthog_settings',
  onSuccess: (ps: PosthogSettings) => initPosthog(ps),
})

let isTelemetryEnabled = () => {
  if (!posthogSettings.data) return false

  return (
    posthogSettings.data.enable_telemetry &&
    posthogSettings.data.posthog_project_id &&
    posthogSettings.data.posthog_host
  )
}

// Posthog Initialization
function initPosthog(ps: PosthogSettings) {
  if (!isTelemetryEnabled()) return

  posthog.init(ps.posthog_project_id, {
    api_host: ps.posthog_host,
    person_profiles: 'identified_only',
    autocapture: false,
    capture_pageview: false,
    capture_pageleave: false,
    enable_heatmaps: false,
    disable_session_recording: true,
    loaded: (ph: typeof posthog) => {
      window.posthog = ph
      ph.identify(window.location.host)
    },
  })
}

// Posthog Functions
function capture(
  event: string,
  options: CaptureOptions = { data: { user: '' } },
) {
  if (!isTelemetryEnabled()) return
  window.posthog.capture(`crm_${event}`, options)
}

function startRecording() {
  if (!isTelemetryEnabled()) return
  if (window.posthog?.__loaded) {
    window.posthog.startSessionRecording()
  }
}

function stopRecording() {
  if (!isTelemetryEnabled()) return
  if (window.posthog?.__loaded && window.posthog.sessionRecordingStarted()) {
    window.posthog.stopSessionRecording()
  }
}

// Posthog Plugin
function posthogPlugin(app: any) {
  app.config.globalProperties.posthog = posthog
  if (!window.posthog?.length) posthogSettings.fetch()
}

export {
  posthog,
  posthogSettings,
  posthogPlugin,
  capture,
  startRecording,
  stopRecording,
}