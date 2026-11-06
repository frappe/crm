<template>
  <SlaPolicyList v-if="step.screen == 'list'" />
  <SlaPolicyView v-else-if="step.screen == 'view'" />
</template>

<script setup>
import SlaPolicyList from './SlaPolicyList.vue'
import SlaPolicyView from './SlaPolicyView.vue'
import { ref, provide, onUnmounted } from 'vue'
import { createListResource } from 'frappe-ui'
import { slaToReopen } from './utils'

const slaSearchQuery = ref('')
const step = ref(
  slaToReopen.value
    ? { screen: 'view', data: { name: slaToReopen.value }, fetchData: true }
    : { screen: 'list', data: null, fetchData: false },
)
slaToReopen.value = null

const slaPolicyListData = createListResource({
  doctype: 'CRM Service Level Agreement',
  fields: ['name', 'default', 'enabled', 'apply_on'],
  cache: ['SLAPolicyList'],
  orderBy: 'modified desc',
  start: 0,
  pageLength: 999,
  auto: true,
})

provide('slaSearchQuery', slaSearchQuery)
provide('slaPolicyListResource', slaPolicyListData)
provide('step', step)
provide('updateStep', updateStep)

function updateStep(newStep, data, fetchData) {
  step.value = { screen: newStep, data, fetchData }
}

onUnmounted(() => {
  slaSearchQuery.value = ''
  slaPolicyListData.filters = {}
})
</script>
