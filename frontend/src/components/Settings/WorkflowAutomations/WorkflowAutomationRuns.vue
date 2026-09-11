<template>
  <div class="min-h-32">
    <div v-if="runs.loading" class="flex justify-center py-8">
      <LoadingIndicator class="w-4" />
    </div>
    <div
      v-else-if="!runs.data?.length"
      class="py-8 text-center text-sm text-ink-gray-5"
    >
      {{ __('No runs yet') }}
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="run in runs.data"
        :key="run.name"
        class="rounded border border-outline-gray-2 p-3"
      >
        <div class="flex items-center justify-between">
          <div class="text-base-medium text-ink-gray-8">
            {{ statusOf(run) }}
          </div>
          <div class="text-xs text-ink-gray-5">{{ run.started_at }}</div>
        </div>
        <div v-if="run.ref_docname" class="mt-1 text-xs text-ink-gray-5">
          {{ run.ref_doctype }} {{ run.ref_docname }}
        </div>
        <div v-if="errorOf(run)" class="mt-1 text-sm text-ink-red-4">
          {{ errorOf(run) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { LoadingIndicator, createListResource } from 'frappe-ui'

const props = defineProps({
  automationName: { type: String, default: '' },
})

// A run is a Background Task named after the flow it executes.
const runs = createListResource({
  doctype: 'Background Task',
  fields: [
    'name',
    'status',
    'started_at',
    'ended_at',
    'ref_doctype',
    'ref_docname',
    'result',
  ],
  filters: { task_name: `Automation Flow: ${props.automationName}` },
  orderBy: 'creation desc',
  pageLength: 20,
  auto: Boolean(props.automationName),
})

function resultOf(run) {
  try {
    return JSON.parse(run.result || '{}')
  } catch {
    return {}
  }
}

function statusOf(run) {
  return resultOf(run).automation_status || run.status
}

function errorOf(run) {
  return resultOf(run).error_summary
}
</script>
