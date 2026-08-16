<template>
  <div class="min-h-32 space-y-4">
    <div class="space-y-2">
      <Link
        v-if="doctype"
        :model-value="docname"
        :doctype="doctype"
        :label="__('Run against')"
        @update:model-value="pickDocument"
      />
      <p class="text-xs text-ink-gray-5">
        {{
          __(
            'The flow runs for real against this document, then everything it did is undone. Nothing is saved, sent or scheduled.',
          )
        }}
      </p>
    </div>

    <div class="flex justify-end">
      <Button
        :label="__('Run')"
        variant="solid"
        :loading="running"
        :disabled="doctype && !docname"
        @click="run"
      />
    </div>

    <div v-if="error" class="text-sm text-ink-red-4" role="alert">
      {{ error }}
    </div>

    <div v-if="result" class="space-y-2">
      <div class="flex items-center gap-2">
        <Badge
          :label="__(result.status)"
          :theme="statusTheme(result.status)"
          variant="subtle"
        />
        <span v-if="result.error_summary" class="text-sm text-ink-red-4">
          {{ result.error_summary }}
        </span>
      </div>

      <div
        v-for="step in result.steps"
        :key="step.step_idx"
        class="rounded border border-outline-gray-2 p-3"
      >
        <div class="flex items-center justify-between">
          <div class="text-base-medium text-ink-gray-8">
            {{ step.action_type }}
          </div>
          <Badge
            :label="__(step.status)"
            :theme="statusTheme(step.status)"
            variant="subtle"
          />
        </div>

        <div v-if="step.message" class="mt-1 text-sm text-ink-red-4">
          {{ step.message }}
        </div>

        <div v-if="step.condition" class="mt-1 space-y-1">
          <code class="block text-xs text-ink-gray-7">{{ step.condition }}</code>
          <div
            v-for="(value, name) in step.condition_values"
            :key="name"
            class="text-xs text-ink-gray-5"
          >
            {{ name }} = {{ JSON.stringify(value) }}
          </div>
        </div>

        <details v-if="step.traceback" class="mt-2">
          <summary class="cursor-pointer text-xs text-ink-gray-5">
            {{ __('Technical details') }}
          </summary>
          <pre class="mt-1 overflow-x-auto text-xs text-ink-gray-6">{{
            step.traceback
          }}</pre>
        </details>
      </div>

      <div
        v-if="!result.steps?.length"
        class="py-4 text-center text-sm text-ink-gray-5"
      >
        {{ __('This flow has no steps to run.') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import { Badge, Button, call } from 'frappe-ui'
import { ref } from 'vue'

const props = defineProps({
  automationName: { type: String, default: '' },
  doctype: { type: String, default: '' },
})

const THEMES = {
  Success: 'green',
  Skipped: 'gray',
  Waiting: 'blue',
  Failed: 'red',
  'Partially Failed': 'orange',
}

const docname = ref('')
const running = ref(false)
const result = ref(null)
const error = ref('')

function pickDocument(value) {
  docname.value = value
  result.value = null
}

async function run() {
  running.value = true
  error.value = ''
  try {
    result.value = await call('frappe.automation_engine.api.trial_run', {
      automation: props.automationName,
      docname: docname.value || null,
    })
  } catch (e) {
    error.value = e.messages?.join('\n') || e.message
  } finally {
    running.value = false
  }
}

function statusTheme(status) {
  return THEMES[status] || 'gray'
}
</script>
