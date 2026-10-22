<template>
  <!-- mounted on first open and kept after, so closing the window keeps the chat -->
  <FloatingWindow
    v-if="flowInstalled && src"
    v-model:mode="mode"
    storage-key="crm-assistant-window"
    data-editor-floating
    :class="[
      assistantOpen ? '' : 'hidden',
      // above Settings and other dialogs, and still clickable while one is open
      '!pointer-events-auto',
      mode === 'docked'
        ? 'relative z-[60] h-full w-[420px] shrink-0 !rounded-none border-l border-outline-gray-2'
        : '!z-[60]',
      // minimized, it's only Flow's icon
      mode === 'minimized' ? '!w-auto !bg-transparent !shadow-none' : '',
    ]"
    @pointerdown.capture="moving = true"
  >
    <template #header="{ dock, float, minimize, expandFromTray }">
      <button
        v-if="mode === 'minimized'"
        class="grid size-10 place-items-center overflow-hidden rounded-[10px] shadow-lg"
        :title="__('Open the assistant')"
        :aria-label="__('Open the assistant')"
        @pointerdown.stop
        @click="expandFromTray"
      >
        <img v-if="flowLogo" :src="flowLogo" alt="" class="size-full" />
        <LucideSparkles v-else class="size-5 text-ink-gray-7" />
      </button>
      <div v-else class="flex items-center justify-between gap-2 px-2.5 py-1.5">
        <div
          class="flex min-w-0 items-center gap-2 text-sm font-medium text-ink-gray-8"
        >
          <LucideSparkles class="size-4 shrink-0 text-ink-gray-6" />
          {{ __('Assistant') }}
        </div>
        <div class="flex shrink-0 items-center gap-1" @pointerdown.stop>
          <Button
            variant="ghost"
            :tooltip="__('Open in a new tab')"
            @click="openFullPage"
          >
            <template #icon><LucideExternalLink class="size-4" /></template>
          </Button>
          <Button
            variant="ghost"
            :tooltip="
              mode === 'docked' ? __('Pop out') : __('Dock to the side')
            "
            @click="mode === 'docked' ? float() : dock()"
          >
            <template #icon>
              <LucidePictureInPicture2
                v-if="mode === 'docked'"
                class="size-4"
              />
              <LucidePanelRight v-else class="size-4" />
            </template>
          </Button>
          <Button variant="ghost" :tooltip="__('Minimize')" @click="minimize">
            <template #icon><LucideMinus class="size-4" /></template>
          </Button>
          <Button
            variant="ghost"
            :tooltip="__('Close')"
            @click="assistantOpen = false"
          >
            <template #icon><LucideX class="size-4" /></template>
          </Button>
        </div>
      </div>
    </template>
    <!-- while the window moves, the chat frame would swallow the pointer -->
    <iframe
      ref="frame"
      :src="src"
      class="size-full border-0"
      :class="{
        'pointer-events-none': moving,
        'rounded-b-6': mode !== 'docked',
      }"
      :title="__('Assistant')"
      @load="keepCrmLinksHere"
    />
  </FloatingWindow>
</template>

<script setup lang="ts">
import {
  assistantOpen,
  assistantPrompt,
  assistantChanges,
  checkFlowInstalled,
  flowInstalled,
  flowLogo,
  openAssistant,
} from '@/composables/assistant'
import {
  changedRecords,
  whereToGo,
  type FlowChange,
} from '@/utils/assistantChanges'
import { reloadDocument } from '@/data/document'
import { unsavedSettings } from '@/composables/settings'
import { Button } from 'frappe-ui'
import { FloatingWindow } from 'frappe-ui/experimental'
import type { WindowMode } from 'frappe-ui/experimental'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LucideExternalLink from '~icons/lucide/external-link'
import LucideMinus from '~icons/lucide/minus'
import LucidePanelRight from '~icons/lucide/panel-right'
import LucidePictureInPicture2 from '~icons/lucide/picture-in-picture-2'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideX from '~icons/lucide/x'

const route = useRoute()
const router = useRouter()
const frame = ref<HTMLIFrameElement | null>(null)
const src = ref('')
// floating by default, like a chat window; it remembers where it was left
const mode = ref<WindowMode>('floating')
const moving = ref(false)

checkFlowInstalled()

watch(
  [assistantOpen, assistantPrompt],
  ([open, prompt]) => {
    if (!open) return
    if (prompt) {
      src.value = `/flow?prompt=${encodeURIComponent(prompt)}`
      assistantPrompt.value = ''
    } else if (!src.value) {
      src.value = '/flow'
    }
  },
  { immediate: true },
)

// ?assistant=<message> opens the panel with that message typed in
watch(
  () => route.query.assistant,
  (prompt) => {
    if (typeof prompt !== 'string') return
    openAssistant(prompt)
    const { assistant, ...query } = route.query
    router.replace({ query })
  },
  { immediate: true },
)

// links to CRM pages open beside the chat instead of in a new tab
function keepCrmLinksHere(): void {
  frame.value?.contentDocument?.addEventListener(
    'click',
    (event) => {
      const link = (event.target as HTMLElement).closest('a')
      if (!link) return
      const url = new URL(link.href, window.location.href)
      // /crm/… only: /crm-form/… is a public page and keeps its new tab
      const crmPage =
        url.pathname === '/crm' || url.pathname.startsWith('/crm/')
      if (url.origin !== window.location.origin || !crmPage) return
      event.preventDefault()
      router.push(url.pathname.replace(/^\/crm/, '') + url.search)
    },
    true,
  )
}

// after each turn, open what the assistant changed: the record, its list or its Settings page
function showChanges(event: MessageEvent): void {
  if (event.source !== frame.value?.contentWindow) return
  if (event.data?.type !== 'flow:changes') return
  const changes = event.data.changes as FlowChange[]
  const changed = changedRecords(changes)
  assistantChanges.value = changed
  changed.records.forEach(({ doctype, name }) => reloadDocument(doctype, name))
  const destination = whereToGo(changes)
  // unsaved edits in Settings stay open; the chat links to what changed
  if (!destination || unsavedSettings.value) return
  if ('settings' in destination) {
    // the chat window sits above the Settings dialog, so the conversation carries on beside it
    const { settings, record } = destination
    router.push({
      query: { ...route.query, settings, ...(record ? { record } : {}) },
    })
  } else {
    router.push(destination.path)
  }
}

function stopMoving(): void {
  moving.value = false
}

onMounted(() => {
  window.addEventListener('message', showChanges)
  window.addEventListener('pointerup', stopMoving)
  window.addEventListener('pointercancel', stopMoving)
})
onBeforeUnmount(() => {
  window.removeEventListener('message', showChanges)
  window.removeEventListener('pointerup', stopMoving)
  window.removeEventListener('pointercancel', stopMoving)
})

function openFullPage(): void {
  window.open(frame.value?.contentWindow?.location.href || '/flow', '_blank')
}
</script>
