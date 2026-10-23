<template>
  <Switch :model-value="enabled" size="sm" @update:model-value="save" />
</template>

<script setup>
import { Switch, call, toast } from 'frappe-ui'
import { ref } from 'vue'

const OPT_OUT_KEY = 'crm_morning_digest'

const enabled = ref(window.sysdefaults?.[OPT_OUT_KEY] !== '0')

async function save(value) {
  enabled.value = value
  try {
    await call('crm.api.home.set_morning_digest', { enabled: value })
    window.sysdefaults = {
      ...window.sysdefaults,
      [OPT_OUT_KEY]: value ? null : '0',
    }
  } catch (error) {
    enabled.value = !value
    toast.error(
      error.messages?.[0] || __('Could not update morning digest setting'),
    )
  }
}
</script>
