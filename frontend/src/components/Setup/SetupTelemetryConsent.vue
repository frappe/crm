<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Share usage data to help us improve Frappe CRM?') }}
    </h1>
    <p class="mt-2 text-p-base text-ink-gray-6">
      {{ __('You can change this anytime in System Settings.') }}
    </p>
    <ErrorMessage class="mt-4" :message="error" />
    <div class="mt-auto flex items-center justify-between gap-3 pt-8">
      <Button
        variant="ghost"
        :label="__('No thanks')"
        :loading="saving"
        :disabled="loading"
        @click="decline"
      />
      <Button
        variant="solid"
        :label="__('Yes, share usage data')"
        :disabled="!ready || saving"
        :loading="loading"
        @click="accept"
      />
    </div>
  </div>
</template>

<script setup>
import { Button, ErrorMessage, call } from 'frappe-ui'
import { telemetryPlugin, useTelemetry } from '@framework/ui/telemetry'
import { getCurrentInstance, onMounted, ref } from 'vue'

const emit = defineEmits(['accepted', 'declined'])
const telemetry = useTelemetry()
const app = getCurrentInstance().appContext.app
const enabled = ref(false)
const loading = ref(true)
const ready = ref(false)
const saving = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    const value = await call('frappe.client.get_single_value', {
      doctype: 'System Settings',
      field: 'enable_telemetry',
    })
    ready.value = true
    enabled.value = Boolean(Number(value))
  } catch (err) {
    error.value = __('Could not load usage data preferences. Please reload to try again.')
    console.error('Failed to load telemetry preference', err)
  } finally {
    loading.value = false
  }
})

async function accept() {
  if (!ready.value || saving.value) return
  if (enabled.value) return emit('accepted')
  await savePreference(true)
}

function decline() {
  return savePreference(false)
}

async function savePreference(share) {
  if (loading.value || saving.value) return
  saving.value = true
  error.value = ''
  try {
    await call('frappe.client.set_value', {
      doctype: 'System Settings',
      name: 'System Settings',
      fieldname: 'enable_telemetry',
      value: share ? 1 : 0,
    })
    await applyPreference(share)
  } catch (err) {
    error.value = __('Could not save your preference. Please try again.')
    console.error('Failed to save telemetry preference', err)
  } finally {
    saving.value = false
  }
}

async function applyPreference(share) {
  if (share) await telemetryPlugin.install(app, { app_name: 'crm' })
  else telemetry.disable()
  emit(share ? 'accepted' : 'declined')
}
</script>
