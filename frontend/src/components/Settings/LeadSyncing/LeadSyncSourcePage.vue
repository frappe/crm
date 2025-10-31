<template>
  <div class="flex-1 p-6">
    <LeadSyncSourceForm
      v-if="step === 'new-source'"
      :sourceData="source"
      @updateStep="updateStep"
    />
    <LeadSyncSources
      v-else-if="step === 'source-list'"
      @updateStep="updateStep"
    />
    <LeadSyncSourceForm
      v-else-if="step === 'edit-source'"
      :sourceData="source"
      @updateStep="updateStep"
    />
  </div>
</template>

<script setup>
import LeadSyncSources from "./LeadSyncSources.vue"
import LeadSyncSourceForm from "./LeadSyncSourceForm.vue";

import { createListResource } from 'frappe-ui'
import { provide, ref } from 'vue'

const step = ref('source-list')
const source = ref(null)

const sources = createListResource({
  type: 'list',
  doctype: 'Lead Sync Source',
  cache: 'lead_sync_sources',
  fields: [
    'name',
    'enabled',
    'type',
    'last_synced_at',
    'facebook_lead_form'
  ],
  auto: true,
  orderBy: 'modified desc',
  pageLength: 20,
})

provide('sources', sources)

function updateStep(newStep, data) {
  step.value = newStep
  source.value = data
}
</script>