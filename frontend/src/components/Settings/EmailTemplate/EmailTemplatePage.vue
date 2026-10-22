<template>
  <NewEmailTemplate
    v-if="step === 'new-template'"
    :templateData="template"
    @updateStep="updateStep"
  />
  <EmailTemplates
    v-else-if="step === 'template-list'"
    @updateStep="updateStep"
  />
  <EditEmailTemplate
    v-else-if="step === 'edit-template'"
    :templateData="template"
    @updateStep="updateStep"
  />
</template>

<script setup>
import NewEmailTemplate from './NewEmailTemplate.vue'
import EditEmailTemplate from './EditEmailTemplate.vue'
import EmailTemplates from './EmailTemplates.vue'
import { useBroadcast } from '@/composables/useBroadcast'
import { settingsRecord } from '@/composables/settings'
import { call, createListResource } from 'frappe-ui'
import { provide, ref, watch } from 'vue'

const step = ref('template-list')
const template = ref(null)

const { on } = useBroadcast()

const templates = createListResource({
  type: 'list',
  doctype: 'Email Template',
  cache: 'emailTemplates',
  fields: [
    'name',
    'enabled',
    'use_html',
    'reference_doctype',
    'subject',
    'response',
    'response_html',
    'modified',
    'owner',
  ],
  auto: true,
  filters: { reference_doctype: ['in', ['CRM Lead', 'CRM Deal']] },
  orderBy: 'modified desc',
  pageLength: 20,
})

provide('templates', templates)

function updateStep(newStep, data) {
  step.value = newStep
  template.value = data
}

on('email_template_page', (data) => {
  step.value = data.page
  template.value = data
})

// Settings opened on one template, such as one the assistant just changed
watch(
  settingsRecord,
  async (name) => {
    if (!name) return
    settingsRecord.value = ''
    templates.reload()
    const doc = await call('frappe.client.get', {
      doctype: 'Email Template',
      name,
    }).catch(() => null)
    if (doc) updateStep('edit-template', doc)
  },
  { immediate: true },
)
</script>
