// Frappe adds the launcher's script only for users who may use Flow, and only on versions that have it.
export function hasFlowLauncher() {
  return Boolean(
    document.querySelector('script[src*="/flow_launcher.bundle."]'),
  )
}
