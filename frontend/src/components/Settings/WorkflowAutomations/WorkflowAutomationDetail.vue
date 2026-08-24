<template>
  <SettingsLayoutBase
    :title="doc.title || __('Automation')"
    :description="triggerSummary"
  >
    <template #title>
      <h2 class="flex h-5 items-center gap-2 text-2xl-semibold leading-none">
        <Button
          variant="ghost"
          icon="lucide-chevron-left"
          :aria-label="__('Back to automations')"
          @click="$emit('back')"
        />
        {{ doc.title || __('Automation') }}
      </h2>
    </template>
    <template #header-actions>
      <div class="flex items-center gap-2">
        <Button
          :label="__('See Runs')"
          icon-left="lucide-history"
          @click="showRuns = true"
        />
        <Button
          :label="__('Edit Automation')"
          variant="solid"
          icon-left="lucide-pencil"
          @click="$emit('edit')"
        />
      </div>
    </template>
    <template #content>
      <div v-if="loading" class="mt-12 flex justify-center">
        <LoadingIndicator class="w-4" />
      </div>
      <div v-else class="space-y-6 pb-6">
        <div class="flex items-center gap-2">
          <Badge
            :label="doc.enabled ? __('Enabled') : __('Draft')"
            :theme="doc.enabled ? 'green' : 'orange'"
            variant="subtle"
          />
          <Badge
            v-if="doc.disabled_reason"
            :label="doc.disabled_reason"
            theme="red"
            variant="subtle"
          />
        </div>

        <section>
          <h3 class="mb-2 text-sm-semibold uppercase text-ink-gray-5">
            {{ __('Flow') }}
          </h3>
          <div
            class="h-[480px] overflow-hidden rounded border border-outline-gray-2"
          >
            <WorkflowFlow :nodes="nodes" :edges="edges" readonly />
          </div>
        </section>

        <ReadOnlySection
          v-if="relationships.length"
          :title="__('Related Records')"
        >
          <ReadOnlyRow
            v-for="item in relationships"
            :key="item.alias"
            :label="item.alias"
            :value="
              __('{0} of {1}', [item.relationship, item.source || 'trigger'])
            "
          />
        </ReadOnlySection>

        <ReadOnlySection :title="__('Settings')">
          <ReadOnlyRow :label="__('Run As')" :value="runAsSummary" />
        </ReadOnlySection>
      </div>
    </template>
  </SettingsLayoutBase>
  <Dialog v-model:open="showRuns" :title="__('Automation Runs')">
    <template #default>
      <AutomationRuns :automation-name="automationName" />
    </template>
  </Dialog>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import AutomationRuns from './WorkflowAutomationRuns.vue'
import ReadOnlyRow from './WorkflowReadOnlyRow.vue'
import ReadOnlySection from './WorkflowReadOnlySection.vue'
import WorkflowFlow from './WorkflowFlow.vue'
import { workflowEdges, workflowNodes } from './workflowGraph'
import { toTree } from './workflowSteps'
import { Badge, Button, Dialog, LoadingIndicator, call } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  automationName: { type: String, required: true },
})

defineEmits(['edit', 'back'])

const loading = ref(false)
const showRuns = ref(false)
const doc = reactive({})

const tree = computed(() => toTree(doc.actions || []))
const graphDoc = computed(() => ({ ...doc, actions: tree.value }))
const nodes = computed(() => workflowNodes(graphDoc.value))
const edges = computed(() => workflowEdges(tree.value))

const relationships = computed(() => {
  try {
    return JSON.parse(doc.relationships || '[]')
  } catch {
    return []
  }
})

const triggerSummary = computed(() => {
  const trigger = (doc.trigger_type || '').replace(/^Doc /, 'Record ')
  if (doc.trigger_type === 'Field Value Changed') {
    return __('{0} changes to {1}', [
      doc.trigger_field,
      doc.to_value || __('any value'),
    ])
  }
  if (doc.trigger_type === 'Custom Event')
    return __('Event {0}', [doc.custom_event])
  if (doc.trigger_type === 'Scheduled')
    return __('Cron {0}', [doc.cron_expression])
  return trigger
})

const runAsSummary = computed(() => {
  if (doc.run_as === 'Automation User')
    return `${doc.run_as} (${doc.automation_user})`
  return doc.run_as
})

watch(() => props.automationName, load, { immediate: true })

async function load() {
  loading.value = true
  try {
    Object.assign(
      doc,
      await call('frappe.client.get', {
        doctype: 'Automation Flow',
        name: props.automationName,
      }),
    )
  } finally {
    loading.value = false
  }
}
</script>
