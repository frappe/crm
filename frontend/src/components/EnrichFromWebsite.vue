<template>
  <!-- Disabled buttons get no hover events, so the tooltip sits on a wrapper.
       tabindex lets keyboard users focus it and see the tooltip too. -->
  <Tooltip v-if="!hasWebsite" :text="__('Add website to auto enrich')">
    <div class="inline-flex" tabindex="0">
      <Button :label="__('Enrich')" iconLeft="lucide-zap" disabled />
    </div>
  </Tooltip>
  <!-- No `loading` prop: it changes the button's look. While running, the
       same Spinner it renders replaces the icon in the prefix, a grey fill
       tracks the real progress, and pointer-events-none + the guard in
       enrich() block repeat clicks. `label` is kept for aria-label. -->
  <Button
    v-else
    :label="running ? __('Enriching…') : __('Enrich')"
    :tooltip="running ? __('Enriching…') : __('Enrich from website')"
    :aria-disabled="running || undefined"
    class="relative isolate overflow-hidden"
    :class="{ 'pointer-events-none': running }"
    @click="enrich"
  >
    <template #prefix>
      <!-- Same technique as frappe-ui's Progress.vue: a full-width fill slid
           left so only `fill`% shows. z-[-1] inside the isolated button keeps
           it above the button background but under the icon and label. -->
      <span
        aria-hidden="true"
        class="absolute inset-0 z-[-1] bg-surface-gray-4"
        :class="{
          'transition-transform ease-[cubic-bezier(0.65,0,0.35,1)] motion-reduce:transition-none':
            running,
        }"
        :style="{
          transform: `translateX(${fill - 100}%)`,
          transitionDuration: `${TICK_MS}ms`,
        }"
      />
      <Spinner v-if="running" class="size-4" aria-hidden="true" />
      <span v-else class="lucide-zap size-4" aria-hidden="true" />
    </template>
    <!-- Both labels share one grid cell so the button is always as wide as the
         longer one and the header doesn't shift when the label changes. -->
    <span class="grid">
      <span class="col-start-1 row-start-1" :class="{ invisible: running }">
        {{ __('Enrich') }}
      </span>
      <span class="col-start-1 row-start-1" :class="{ invisible: !running }">
        {{ __('Enriching…') }}
      </span>
    </span>
  </Button>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { Button, Spinner, Tooltip, call, toast } from 'frappe-ui'
import { useTelemetry } from '@framework/ui/telemetry'
import { useDocument } from '@/data/document'
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
// Shared per-record document resource. `enriching` on it lets the Data tab
// disable Save during a run, so it can't collide with the job's own save.
const { document } = useDocument(props.doctype, props.docname)
const EVENT = 'domain_enrichment_progress'

const running = ref(false)
// Fill width in percent (0–100). Only animated while running, so resetting it
// to 0 snaps back instead of sliding.
const fill = ref(0)
let creepTimer = null
let finishTimer = null

// Fill shown right after the click, before the first socket event arrives.
const START_FILL = 8
// Running events never fill past this; the last stretch is for 'completed'.
const MAX_RUNNING_FILL = 90
// Also the fill's transition duration, so each creep step lands before the next.
const TICK_MS = 660
// How long the full fill stays visible before the button goes back to normal.
const HOLD_MS = 500
// Ceiling the fill may creep up to while waiting on the current step: just
// short of where the next step would put it.
let creepCeiling = START_FILL

const hasWebsite = computed(() => Boolean((props.website || '').trim()))

function isForThisDoc(data) {
  return (
    data &&
    data.reference_doctype === props.doctype &&
    data.reference_name === props.docname
  )
}

// Fill for a running event. Steps are 0-based (0 … total-1), spread evenly
// between START_FILL and MAX_RUNNING_FILL.
function fillForStep(step, total) {
  if (!total || total < 2) return START_FILL
  const ratio = Math.min(Math.max(step / (total - 1), 0), 1)
  return START_FILL + ratio * (MAX_RUNNING_FILL - START_FILL)
}

function setStep(step, total) {
  const next = Math.min(step + 1, total - 1)
  fill.value = Math.max(fill.value, fillForStep(step, total))
  creepCeiling = Math.max(creepCeiling, fillForStep(next, total) - 2)
}

function startCreep() {
  // Steps can be far apart (crawling is the long one), so ease the fill toward
  // the next step's mark instead of sitting still between events.
  creepTimer = setInterval(() => {
    if (fill.value < creepCeiling) {
      fill.value += Math.max((creepCeiling - fill.value) * 0.1, 0.2)
      fill.value = Math.min(fill.value, creepCeiling)
    }
  }, TICK_MS)
}

function clearTimers() {
  clearInterval(creepTimer)
  clearTimeout(finishTimer)
  creepTimer = null
  finishTimer = null
}

// Stop listening and creeping but keep the running look, so the completed
// fill can finish and hold before reset().
function stop() {
  $socket.off(EVENT, onProgress)
  clearInterval(creepTimer)
  creepTimer = null
}

function reset() {
  stop()
  clearTimers()
  running.value = false
  document.enriching = false
  fill.value = 0
  creepCeiling = START_FILL
}

function finish(payload) {
  reset()
  const filled = (payload && payload.filled_fields) || []
  const notes = (payload && payload.notes) || []
  if (filled.length) {
    toast.success(__('Enriched. Filled: {0}', [filled.join(', ')]))
  } else if (notes.length) {
    // Nothing extracted — explain why (blocked / JS-only site).
    toast.warning(notes[0])
  } else {
    toast.success(__('Enrichment complete.'))
  }
  emit('done') // parent reloads the document + side panel — no manual refresh
}

function onProgress(data) {
  if (!isForThisDoc(data) || !running.value) return
  if (data.status === 'running') {
    // Only step/total drive the fill; crawl messages are never shown.
    setStep(Number(data.step) || 0, Number(data.total) || 0)
  } else if (data.status === 'completed') {
    stop()
    fill.value = 100
    // Re-validate the cached organizations store so list views (whose logos/names
    // are read from it) reflect this update even if no list page was open to catch
    // the event — otherwise navigating back to a list serves stale cached data.
    organizations.reload()
    // Let the fill reach 100%, hold it there with the "Enriching…" label, then
    // finish. Cleared on unmount, so nothing fires on a dead component.
    finishTimer = setTimeout(() => finish(data.payload), TICK_MS + HOLD_MS)
  } else if (data.status === 'error') {
    reset()
    toast.error(data.message || __('Enrichment failed.'))
  }
}

async function enrich() {
  // Keyboard activation still reaches here while running.
  if (running.value || !hasWebsite.value) return

  capture('enrichment_triggered', { doctype: props.doctype })
  clearTimers()
  running.value = true
  document.enriching = true
  // Set in the same tick the transition turns on, so it slides in from 0.
  fill.value = START_FILL
  creepCeiling = START_FILL
  startCreep()
  // Subscribe before enqueueing so we never miss the completion event.
  $socket.on(EVENT, onProgress)

  try {
    await call('crm.domain_enrichment.api.enrich', {
      reference_doctype: props.doctype,
      reference_name: props.docname,
    })
  } catch (error) {
    reset()
    toast.error(error.messages?.[0] || __('Could not start enrichment.'))
  }
}

onBeforeUnmount(reset)
</script>
