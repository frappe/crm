<template>
  <SlaPolicyList v-if="slaActiveStep.screen == 'list'" />
  <SlaPolicyView v-else-if="slaActiveStep.screen == 'view'" />
</template>

<script setup>
import SlaPolicyList from './SlaPolicyList.vue'
import SlaPolicyView from './SlaPolicyView.vue'
import { ref, provide, onUnmounted } from 'vue'
import { createListResource } from 'frappe-ui'
import { slaActiveStep } from './utils'

const slaSearchQuery = ref('')

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

onUnmounted(() => {
  slaSearchQuery.value = ''
  slaPolicyListData.filters = {}
})
</script>
