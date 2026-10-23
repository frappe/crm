<template>
  <div>
    <Checkbox
      :model-value="enabled"
      :disabled="loading || saving"
      :label="__('Share usage data')"
      @update:model-value="savePreference"
    />
    <ErrorMessage class="mt-1" :message="error" />
  </div>
</template>

<script setup>
import { Checkbox, ErrorMessage, call } from 'frappe-ui'
import { telemetryPlugin, useTelemetry } from '@framework/ui/telemetry'
import { getCurrentInstance, ref } from 'vue'

const telemetry = useTelemetry()
const app = getCurrentInstance().appContext.app
const enabled = ref(true)
const loading = ref(true)
const saving = ref(false)
const error = ref('')

const loaded = call('frappe.client.get_single_value', {
  doctype: 'System Settings',
  field: 'enable_telemetry',
})
  .then((value) => (enabled.value = Boolean(value)))
  .catch((err) => console.error('Failed to load telemetry preference', err))
  .finally(() => (loading.value = false))

async function persistPreference(share) {
  await call('frappe.client.set_value', {
    doctype: 'System Settings',
    name: 'System Settings',
    fieldname: 'enable_telemetry',
    value: share ? 1 : 0,
  })
  if (share) await telemetryPlugin.install(app, { app_name: 'crm' })
  else telemetry.disable()
}

async function savePreference(share) {
  if (saving.value) return false
  saving.value = true
  error.value = ''
  try {
    await persistPreference(share)
    enabled.value = share
    return true
  } catch (err) {
    error.value = __('Could not save your preference. Please try again.')
    console.error('Failed to save telemetry preference', err)
    return false
  } finally {
    saving.value = false
  }
}

defineExpose({
  confirm: async () => {
    await loaded
    return savePreference(enabled.value)
  },
})
</script>
