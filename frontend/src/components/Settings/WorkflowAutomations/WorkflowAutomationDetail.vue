<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-start gap-2">
        <Button
          class="-ml-2 shrink-0"
          variant="ghost"
          icon="lucide-chevron-left"
          :aria-label="__('Back to automations')"
          @click="$emit('back')"
        />
        <div class="flex min-w-0 flex-col gap-1">
          <!-- min-h-7 matches the back button, so top-aligning centres them on each other. -->
          <div class="flex min-h-7 items-center gap-2">
            <h2 class="truncate text-2xl-semibold">
              {{ doc.title || __('Automation') }}
            </h2>
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
          <p class="text-p-base text-ink-gray-6">{{ triggerSummary }}</p>
        </div>
      </div>
    </template>
    <template #header-actions>
      <Button
        :label="__('Edit Automation')"
        variant="solid"
        icon-left="lucide-pencil"
        @click="$emit('edit')"
      />
    </template>
    <template #content>
      <div v-if="loading" class="mt-12 flex justify-center">
        <LoadingIndicator class="w-4" />
      </div>
      <div
        v-else
        class="h-full min-h-[480px] overflow-hidden rounded border border-outline-gray-2"
      >
        <WorkflowFlow :nodes="nodes" :edges="edges" readonly />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import WorkflowFlow from './WorkflowFlow.vue'
import { workflowEdges, workflowNodes } from './workflowGraph'
import { toTree } from './workflowSteps'
import { Badge, Button, LoadingIndicator, call } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const props = defineProps({
  automationName: { type: String, required: true },
})

defineEmits(['edit', 'back'])

const loading = ref(false)
const doc = reactive({})

const tree = computed(() => toTree(doc.actions || []))
const graphDoc = computed(() => ({ ...doc, actions: tree.value }))
const nodes = computed(() => workflowNodes(graphDoc.value))
const edges = computed(() => workflowEdges(tree.value))

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
