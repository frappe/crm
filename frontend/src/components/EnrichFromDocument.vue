<template>
  <Tooltip :text="tooltip">
    <div class="inline-flex">
      <Button
        :label="__('Enrich from CNPJ')"
        :loading="running"
        :loadingText="__('Enriching')"
        :disabled="disabled"
        iconLeft="briefcase"
        @click="enrich"
      />
    </div>
  </Tooltip>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Button, call, toast, Tooltip } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { globalStore } from '@/stores/global'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, required: true },
  taxId: { type: String, default: '' },
})

const emit = defineEmits(['done'])

const { $socket } = globalStore()
const { capture } = useTelemetry()
const EVENT = 'registry_enrichment_progress'

const running = ref(false)
const settingsReady = ref(false)

const hasTaxId = computed(() => Boolean((props.taxId || '').trim()))

const disabled = computed(
  () => running.value || !hasTaxId.value || !settingsReady.value,
)

const tooltip = computed(() => {
  if (running.value) return __('Enriching…')
  if (!hasTaxId.value) return __('Set a CNPJ on this record before enriching')
  if (!settingsReady.value)
    return __('Set up CNPJ enrichment in Settings > Integrations')
  return __('Enrich from CNPJ')
})

async function loadStatus() {
  try {
    const status = await call('crm.registry_enrichment.api.get_settings_status')
    settingsReady.value = Boolean(status?.enabled && status?.has_token)
  } catch {
    settingsReady.value = false
  }
}

function isForThisDoc(data) {
  return (
    data &&
    data.reference_doctype === props.doctype &&
    data.reference_name === props.docname
  )
}

function stop() {
  running.value = false
  $socket.off(EVENT, onProgress)
}

function onProgress(data) {
  if (!isForThisDoc(data)) return
  if (data.status === 'completed') {
    stop()
    const count = Number(data.fields_updated || 0)
    if (count > 0) {
      toast.success(__('Enriched. Updated {0} fields.', [count]))
    } else {
      toast.warning(__('No new fields to fill from this CNPJ.'))
    }
    emit('done')
  } else if (data.status === 'failed') {
    stop()
    toast.error(data.error || __('Enrichment failed.'))
  }
}

async function enrich() {
  if (!hasTaxId.value) {
    toast.warning(__('Set a CNPJ on this record before enriching.'))
    return
  }

  capture('registry_enrichment_triggered', { doctype: props.doctype })
  running.value = true
  $socket.on(EVENT, onProgress)

  try {
    await call('crm.registry_enrichment.api.enrich', {
      reference_doctype: props.doctype,
      reference_name: props.docname,
    })
  } catch (error) {
    stop()
    toast.error(error.messages?.[0] || __('Could not start enrichment.'))
  }
}

onMounted(loadStatus)
onBeforeUnmount(() => $socket.off(EVENT, onProgress))
</script>
