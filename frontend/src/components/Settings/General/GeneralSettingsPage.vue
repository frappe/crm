<template>
  <component :is="getComponent(step)" :data="data" @updateStep="updateStep" />
</template>

<script setup>
import GeneralSettings from './GeneralSettings.vue'
import CurrencySettings from './CurrencySettings.vue'
import BrandSettings from './BrandSettings.vue'
import HomeActions from './HomeActions.vue'
import { ref } from 'vue'

const step = ref('general-settings')
const data = ref(null)

function updateStep(newStep, _data) {
  step.value = newStep
  data.value = _data
}

function getComponent(step) {
  switch (step) {
    case 'general-settings':
      return GeneralSettings
    case 'currency-settings':
      return CurrencySettings
    case 'brand-settings':
      return BrandSettings
    case 'home-actions':
      return HomeActions
    default:
      return null
  }
}
</script>
