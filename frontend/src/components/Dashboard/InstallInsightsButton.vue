<template>
  <Tooltip
    v-if="cloud.available || isFcSite"
    :text="__('Install Insights to build custom dashboards')"
  >
    <Button
      :label="__('Install Insights')"
      :iconLeft="InsightsIcon"
      :loading="cloud.opening.value"
      @click="install"
    />
  </Tooltip>
</template>

<script setup>
import InsightsIcon from '@/components/Icons/InsightsIcon.vue'
import { useCloudSettings } from '@/composables/cloudSettings'
import { confirmLoginToFrappeCloud } from '@/composables/frappecloud'
import { Button, Tooltip } from 'frappe-ui'

// both are only set for System Managers
const cloud = useCloudSettings()
const isFcSite = Boolean(window.is_fc_site)

function install() {
  if (cloud.available) cloud.open('marketplace')
  else confirmLoginToFrappeCloud('/apps')
}
</script>
