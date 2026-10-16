<template>
  <div class="flex flex-col">
    <h1 class="text-2xl-semibold text-ink-gray-9">
      {{ __('Import leads from CSV') }}
    </h1>
    <Stepper
      v-model="stage"
      class="mt-3"
      :steps="stages"
      :loading="busy"
      :completed="['Success', 'Partial Success'].includes(result?.status)"
      :aria-label="__('Import steps')"
    />

    <div class="mt-6 flex flex-1 flex-col">
      <SetupImportUpload
        ref="uploadView"
        v-if="stage === 'upload'"
        :class="{ 'pointer-events-none opacity-60': busy }"
        @uploaded="onUploaded"
      />
      <SetupImportMap
        v-else-if="stage === 'map'"
        class="flex-1"
        :preview="preview"
        :saving="busy"
        @continue="onMapped"
      />
      <SetupImportReview
        v-else
        class="flex-1"
        :preview="preview"
        :importing="busy"
        :progress="progress"
        :result="result"
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
import Stepper from '@/components/Stepper/Stepper.vue'
import { useLeadImport } from '@/composables/leadImport'
import { toast } from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { inject, onUnmounted, ref, watchEffect } from 'vue'

const emit = defineEmits(['imported', 'cancel'])

const stages = [
  { value: 'upload', label: __('Upload') },
  { value: 'map', label: __('Map columns') },
  { value: 'review', label: __('Review') },
]

const { capture } = useTelemetry()
const { preview, progress, createImport, saveMapping, runImport } =
  useLeadImport()

const stage = ref('upload')
const uploadView = ref(null)
const busy = ref(false)
const result = ref(null)
const fileName = ref('')

const previewState = inject('setupPreview', null)
watchEffect(() => {
  if (!previewState) return
  const importing = busy.value && stage.value === 'review' && !result.value
  previewState.importStage = importing ? 'importing' : stage.value
  previewState.importFile = fileName.value
  previewState.importRows = preview.value?.total_number_of_rows || 0
  previewState.importProgress = progress.value
  previewState.importResult = result.value && {
    imported: result.value.imported,
    failed: result.value.failedRows.length,
  }
})
onUnmounted(() => previewState && (previewState.importStage = null))

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
  fileName.value = decodeURIComponent(fileUrl.split('/').pop())
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

function back() {
  if (busy.value || uploadView.value?.uploading) return
  if (stage.value === 'review') stage.value = 'map'
  else if (stage.value === 'map') restart()
  else emit('cancel')
}

defineExpose({ back })

function restart() {
  result.value = null
  fileName.value = ''
  stage.value = 'upload'
}
</script>
