<template>
  <!-- While running, show only a spinner (no crawl details). -->
  <Button
    :label="running ? '' : __('Enrich')"
    :loading="running"
    :disabled="running"
    :tooltip="running ? __('Enriching…') : __('Enrich from website')"
    @click="enrich"
  >
    <template v-if="!running" #prefix>
      <FeatherIcon name="zap" class="h-4 w-4" />
    </template>
  </Button>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'
import { Button, FeatherIcon, call, toast } from 'frappe-ui'
import { useTelemetry } from 'frappe-ui/frappe'
import { globalStore } from '@/stores/global'
import { organizationsStore } from '@/stores/organizations'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, required: true },
  website: { type: String, default: '' },
})

const emit = defineEmits(['done'])

const { $socket } = globalStore()
const { organizations } = organizationsStore()
const { capture } = useTelemetry()
const EVENT = 'domain_enrichment_progress'

const running = ref(false)

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
  // Intermediate steps are intentionally ignored — the button shows only a
  // spinner, never the crawl details. We act only on terminal states.
  if (data.status === 'completed') {
    stop()
    // Re-validate the cached organizations store so list views (whose logos/names
    // are read from it) reflect this update even if no list page was open to catch
    // the event — otherwise navigating back to a list serves stale cached data.
    organizations.reload()
    const filled = (data.payload && data.payload.filled_fields) || []
    const notes = (data.payload && data.payload.notes) || []
    if (filled.length) {
      toast.success(__('Enriched. Filled: {0}', [filled.join(', ')]))
    } else if (notes.length) {
      // Nothing extracted — explain why (blocked / JS-only site).
      toast.warning(notes[0])
    } else {
      toast.success(__('Enrichment complete.'))
    }
    emit('done') // parent reloads the document + side panel — no manual refresh
  } else if (data.status === 'error') {
    stop()
    toast.error(data.message || __('Enrichment failed.'))
  }
}

async function enrich() {
  if (!(props.website || '').trim()) {
    toast.warning(__('Set a Website on this record before enriching.'))
    return
  }

  capture('enrichment_quick_triggered', {
    doctype: props.doctype,
    source: 'detail',
  })
  running.value = true
  // Subscribe before enqueueing so we never miss the completion event.
  $socket.on(EVENT, onProgress)

  try {
    await call('crm.domain_enrichment.api.enrich', {
      reference_doctype: props.doctype,
      reference_name: props.docname,
    })
  } catch (error) {
    stop()
    toast.error(error.messages?.[0] || __('Could not start enrichment.'))
  }
}

onBeforeUnmount(() => $socket.off(EVENT, onProgress))
</script>
