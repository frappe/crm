<template>
  <!-- Hidden while enriching; the run being undone is the one in progress. -->
  <Button
    v-if="canUndo && !running"
    :label="__('Undo')"
    :tooltip="__('Undo last enrichment')"
    iconLeft="lucide-undo-2"
    :disabled="undoing"
    @click="confirmUndo"
  />
  <!-- Disabled buttons get no hover events, so the tooltip sits on a wrapper.
       tabindex lets keyboard users focus it and see the tooltip too. -->
  <Tooltip v-if="!hasWebsite" :text="__('Add website to auto enrich')">
    <div class="inline-flex" tabindex="0">
      <Button :label="__('Enrich')" iconLeft="lucide-zap" disabled />
    </div>
  </Tooltip>
  <!-- No `loading` prop: it changes the button's look. While running, the
       same Spinner it renders replaces iconLeft through the prefix slot, a
       grey fill tracks the real progress, and pointer-events-none + the guard
       in enrich() block repeat clicks. -->
  <Button
    v-else
    :label="label"
    :tooltip="tooltip"
    iconLeft="lucide-zap"
    :aria-disabled="running || undefined"
    :disabled="undoing"
    class="relative isolate overflow-hidden"
    :class="{ 'pointer-events-none': running }"
    @click="enrich"
  >
    <template v-if="running" #prefix>
      <Spinner class="size-4" aria-hidden="true" />
    </template>
    <!-- In the suffix only so it doesn't displace iconLeft; it's absolutely
         positioned, so where it sits in the button doesn't matter. -->
    <template #suffix>
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
    </template>
  </Button>
</template>

<script setup>
import { ref, computed, h, onMounted, onBeforeUnmount } from 'vue'
import { Button, Spinner, Tooltip, call, toast } from 'frappe-ui'
import Icon from '@/components/Icon.vue'
import { useTelemetry } from '@framework/ui/telemetry'
import { useDocument } from '@/data/document'
import { reloadEnrichedFields } from '@/data/enrichedFields'
import { createDialog } from '@/utils/dialogs'
import { getMeta } from '@/stores/meta'
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
const { doctypeMeta } = getMeta(props.doctype)
// Shared per-record document resource. `enriching` on it lets the Data tab
// disable Save during a run, so it can't collide with the job's own save.
const { document } = useDocument(props.doctype, props.docname)
const EVENT = 'domain_enrichment_progress'

const running = ref(false)
// From api.get_status: the latest run can be undone.
const canUndo = ref(false)
// From api.get_status: 'idle' | 'running' | 'done'. 'done' means the latest
// run Completed, so the button offers Re-enrich.
const state = ref('idle')
const undoing = ref(false)
// Fill width in percent (0–100). Only animated while running, so resetting it
// to 0 snaps back instead of sliding.
const fill = ref(0)
let creepTimer = null
let checking = false
let finishTimer = null
// Only set when the page opened mid-run (see resume()).
let pollTimer = null
let unmounted = false

// Fill shown right after the click, before the first socket event arrives.
const START_FILL = 8
// Running events never fill past this; the last stretch is for 'completed'.
const MAX_RUNNING_FILL = 90
// Also the fill's transition duration, so each creep step lands before the next.
const TICK_MS = 660
// How long the full fill stays visible before the button goes back to normal.
const HOLD_MS = 500
// How often to re-check a run this tab didn't start, whose socket events
// only reach the user who started it.
const POLL_MS = 3000
// Ceiling the fill may creep up to while waiting on the current step: just
// short of where the next step would put it.
let creepCeiling = START_FILL

const hasWebsite = computed(() => Boolean((props.website || '').trim()))

const label = computed(() => {
  if (running.value) return __('Enriching…')
  return state.value === 'done' ? __('Re-enrich') : __('Enrich')
})
const tooltip = computed(() => {
  if (running.value) return __('Enriching…')
  return state.value === 'done'
    ? __('Re-enrich from website')
    : __('Enrich from website')
})

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
  clearInterval(pollTimer)
  creepTimer = null
  finishTimer = null
  pollTimer = null
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
  if (notes.length && !filled.length) {
    // Nothing extracted — explain why (blocked / JS-only site).
    toast.warning(notes[0])
  } else {
    // Lightning icon as in the Figma toast, passed the way scriptToast does.
    toast.success(__('Enrichment successful'), {
      icon: () => h(Icon, { icon: 'lucide-zap', class: 'size-4' }),
      description: filled.length
        ? __('Filled: {0}', [filled.join(', ')])
        : undefined,
    })
  }
  afterChange()
}

// Refresh everything a finished run or an undo changes.
function afterChange() {
  reloadEnrichedFields(props.doctype, props.docname)
  // Re-validate the cached organizations store so list views (whose logos/names
  // are read from it) reflect this update even if no list page was open to catch
  // it — otherwise navigating back to a list serves stale cached data.
  organizations.reload()
  emit('done') // parent reloads the document + side panel — no manual refresh
  loadStatus()
}

async function loadStatus() {
  try {
    const status = await call('crm.domain_enrichment.api.get_status', {
      reference_doctype: props.doctype,
      reference_name: props.docname,
    })
    canUndo.value = Boolean(status.can_undo)
    state.value = status.state
    return status
  } catch {
    // Status only adds Undo, Re-enrich and the resumed state; the button
    // works without it.
    return null
  }
}

// The page opened while a run is going (e.g. refreshed mid-run): show it as
// Enriching. The socket still finishes it for the user who started the run;
// polling covers everyone else.
function resume() {
  begin()
  pollTimer = setInterval(poll, POLL_MS)
}

async function poll() {
  const status = await loadStatus()
  // pollTimer is cleared on reset/unmount; finishTimer means the socket's
  // 'completed' event already got here.
  if (!pollTimer || finishTimer || !status || status.state === 'running') return
  // Not 'done' means the run failed: no full fill to show, go straight back.
  if (status.state !== 'done') {
    toast.error(__('Enrichment failed.'))
    reset()
    afterChange()
    return
  }
  stop()
  fill.value = 100
  // No payload to report from here, so finish without a toast.
  finishTimer = setTimeout(() => {
    reset()
    afterChange()
  }, TICK_MS + HOLD_MS)
}

function onProgress(data) {
  if (!isForThisDoc(data) || !running.value) return
  if (data.status === 'running') {
    // Only step/total drive the fill; crawl messages are never shown.
    setStep(Number(data.step) || 0, Number(data.total) || 0)
  } else if (data.status === 'completed') {
    stop()
    fill.value = 100
    // Let the fill reach 100%, hold it there with the "Enriching…" label, then
    // finish. Cleared on unmount, so nothing fires on a dead component.
    finishTimer = setTimeout(() => finish(data.payload), TICK_MS + HOLD_MS)
  } else if (data.status === 'error') {
    reset()
    toast.error(data.message || __('Enrichment failed.'))
  }
}

// Labels of fields the user edited since the last run that re-enriching would
// overwrite. "Fill if empty" fields keep the user's value, so they aren't listed.
async function overwrittenEdits() {
  const fields = await call('crm.domain_enrichment.api.get_enriched_fields', {
    reference_doctype: props.doctype,
    reference_name: props.docname,
  })
  return fields.filter((f) => f.edited && f.refreshes).map((f) => f.label)
}

async function enrich() {
  // Keyboard activation still reaches here while running; `checking` stops a
  // second click during the edit check from opening a second dialog.
  if (running.value || undoing.value || checking || !hasWebsite.value) return

  let edited
  checking = true
  try {
    edited = await overwrittenEdits()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not start enrichment.'))
    return
  } finally {
    checking = false
  }
  // The user may have left the page while the edit check was in flight.
  if (unmounted) return
  if (!edited.length) return start()

  createDialog({
    title: __('Overwrite your edits?'),
    message: __(
      'You edited these fields after the last enrichment. Enriching again will replace them with values from the website: {0}',
      [edited.join(', ')],
    ),
    size: 'sm',
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: __('Enrich'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          if (!unmounted) start()
        },
      },
    ],
  })
}

async function start() {
  capture('enrichment_triggered', { doctype: props.doctype })
  begin()

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

// Enter the Enriching state and start listening for progress.
function begin() {
  clearTimers()
  running.value = true
  document.enriching = true
  // Set in the same tick the transition turns on, so it slides in from 0.
  fill.value = START_FILL
  creepCeiling = START_FILL
  startCreep()
  // Subscribe before enqueueing so we never miss the completion event.
  $socket.on(EVENT, onProgress)
}

function confirmUndo() {
  if (running.value || undoing.value || checking) return
  createDialog({
    title: __('Undo enrichment?'),
    message: __(
      'This restores the values these fields had before the last enrichment.',
    ),
    size: 'sm',
    actions: [
      { label: __('Cancel'), onClick: ({ close }) => close() },
      {
        label: __('Undo'),
        variant: 'solid',
        onClick: ({ close }) => {
          close()
          undo()
        },
      },
    ],
  })
}

function fieldLabel(fieldname) {
  const df = doctypeMeta.value?.fields?.find((f) => f.fieldname === fieldname)
  return df?.label ? __(df.label) : fieldname
}

async function undo() {
  if (running.value || undoing.value) return
  undoing.value = true
  // Same flag as a run: keeps the Data tab's Save off while the undo saves.
  document.enriching = true
  try {
    const { reverted = [], skipped = [] } = await call(
      'crm.domain_enrichment.api.undo',
      { reference_doctype: props.doctype, reference_name: props.docname },
    )
    if (!reverted.length) {
      toast.warning(__("Nothing to undo, you've edited all enriched fields"))
    } else if (skipped.length) {
      toast.success(
        __('Enrichment undone. Kept your edits to: {0}', [
          skipped.map(fieldLabel).join(', '),
        ]),
      )
    } else {
      toast.success(__('Enrichment undone'))
    }
    afterChange()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not undo enrichment.'))
    loadStatus()
  } finally {
    undoing.value = false
    document.enriching = false
  }
}

onMounted(async () => {
  const status = await loadStatus()
  // Skip if the user already clicked Enrich while status was loading.
  if (status?.state === 'running' && !running.value && !unmounted) resume()
})

onBeforeUnmount(() => {
  unmounted = true
  reset()
})
</script>
