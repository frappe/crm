<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Import leads from CSV') }}
    </h1>
    <ol
      class="mt-3 flex items-center gap-2 text-sm"
      :aria-label="__('Import steps')"
    >
      <li
        v-for="(label, key) in stages"
        :key="key"
        class="rounded-full px-2 py-0.5"
        :class="
          stage === key
            ? 'bg-surface-gray-9 text-ink-white'
            : 'bg-surface-gray-2 text-ink-gray-6'
        "
        :aria-current="stage === key ? 'step' : undefined"
      >
        {{ label }}
      </li>
    </ol>

    <div class="mt-6 flex flex-1 flex-col">
      <SetupImportUpload
        v-if="stage === 'upload'"
        :class="{ 'pointer-events-none opacity-60': busy }"
        @uploaded="onUploaded"
        @cancel="emit('cancel')"
      />
      <SetupImportMap
        v-else-if="stage === 'map'"
        class="flex-1"
        :preview="preview"
        :saving="busy"
        @back="restart"
        @continue="onMapped"
      />
      <SetupImportReview
        v-else
        class="flex-1"
        :preview="preview"
        :importing="busy"
        :progress="progress"
        :result="result"
        @back="stage = 'map'"
        @import="onImport"
        @restart="restart"
        @continue="emit('imported', result)"
      />
    </div>
  </div>
</template>

<script setup>
import SetupImportUpload from '@/components/Setup/SetupImportUpload.vue'
import SetupImportMap from '@/components/Setup/SetupImportMap.vue'
import SetupImportReview from '@/components/Setup/SetupImportReview.vue'
import { useLeadImport } from '@/composables/leadImport'
import { toast } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { ref } from 'vue'

const emit = defineEmits(['imported', 'cancel'])

const stages = {
  upload: __('Upload'),
  map: __('Map columns'),
  review: __('Review'),
}

const { capture } = useTelemetry()
const { preview, progress, createImport, saveMapping, runImport } =
  useLeadImport()

const stage = ref('upload')
const busy = ref(false)
const result = ref(null)

async function withBusy(action) {
  busy.value = true
  try {
    await action()
  } catch (error) {
    toast.error(
      error.messages?.[0] || error.message || __('Something went wrong'),
    )
    console.error(error)
  } finally {
    busy.value = false
  }
}

function onUploaded(fileUrl) {
  withBusy(async () => {
    await createImport(fileUrl)
    stage.value = 'map'
  })
}

function onMapped(mappings) {
  withBusy(async () => {
    await saveMapping(mappings)
    stage.value = 'review'
  })
}

function onImport() {
  capture('setup_import_started', { rows: preview.value.total_number_of_rows })
  withBusy(async () => {
    result.value = await runImport().catch((error) => {
      capture('setup_import_failed')
      throw error
    })
    capture('setup_import_completed', {
      status: result.value.status,
      imported: result.value.imported,
      failed: result.value.failedRows.length,
    })
  })
}

function restart() {
  result.value = null
  stage.value = 'upload'
}
</script>
