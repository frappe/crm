<template>
  <div
    class="flex flex-col"
    :class="{ 'crm-command-palette': inPalette }"
    @keydown.esc="onEscape"
  >
    <div
      class="flex h-11 shrink-0 items-center gap-1 px-2"
      :class="{ 'border-b border-outline-gray-1': inPalette }"
    >
      <Button
        v-if="inPalette"
        variant="ghost"
        icon-left="lucide-chevron-left"
        :label="__('Search')"
        @click="backToSearch"
      />
      <span
        v-else
        class="flex items-center gap-1.5 ps-3 text-sm text-ink-gray-5"
      >
        <LucideSparkles class="size-3.5" />
        {{ __('Flow') }}
      </span>
      <div class="ms-auto flex items-center gap-1">
        <ChatHistory />
        <Button
          variant="ghost"
          icon="lucide-plus"
          :tooltip="__('New chat')"
          :aria-label="__('New chat')"
          @click="startNewChat"
        />
        <Button
          v-if="askFlow.session"
          variant="ghost"
          icon-right="lucide-arrow-up-right"
          :label="__('Open in Flow')"
          @click="handOff"
        />
      </div>
    </div>

    <div
      class="max-h-[420px] min-h-[8rem] overflow-y-auto px-5 pb-5"
      :class="inPalette ? 'pt-4' : 'pt-1'"
    >
      <template v-if="askFlow.earlier.length">
        <button
          type="button"
          class="-ms-1 mb-3 flex items-center gap-1 rounded-4 px-1 py-0.5 text-sm text-ink-gray-5 hover:text-ink-gray-8"
          @click="showEarlier = !showEarlier"
        >
          <component
            :is="showEarlier ? LucideChevronDown : LucideChevronUp"
            class="size-3.5"
          />
          {{ earlierLabel }}
        </button>
        <div
          v-if="showEarlier"
          class="mb-4 flex flex-col gap-4 border-b border-outline-gray-1 pb-4"
        >
          <div v-for="(turn, index) in askFlow.earlier" :key="index">
            <div class="pb-1.5 text-base font-medium text-ink-gray-9">
              {{ capitalize(turn.question) }}
            </div>
            <FlowAnswer :text="turn.answer" />
          </div>
        </div>
      </template>

      <div
        v-if="askFlow.status === 'loading'"
        class="flex items-center gap-2 text-base text-ink-gray-5"
      >
        <LucideLoaderCircle class="size-4 shrink-0 animate-spin" />
        {{ __('Opening chat…') }}
      </div>
      <h2 v-else class="text-lg font-semibold leading-snug text-ink-gray-9">
        {{ capitalize(askFlow.question) }}
      </h2>
      <div
        v-if="askFlow.context || askFlow.seconds"
        class="flex items-center gap-2 pt-1.5 text-sm text-ink-gray-5"
      >
        <span
          v-if="askFlow.context && askFlow.useContext"
          class="flex items-center gap-1 rounded-4 bg-surface-gray-2 px-1.5 py-0.5 text-xs text-ink-gray-6"
        >
          {{ contextLabel }}
          <button
            type="button"
            class="text-ink-gray-4 hover:text-ink-gray-7"
            :aria-label="__('Leave this record out of follow-ups')"
            @click="askFlow.useContext = false"
          >
            <LucideX class="size-3" />
          </button>
        </span>
        <span v-if="askFlow.seconds">
          {{ __('Flow · {0} s', [askFlow.seconds]) }}
        </span>
      </div>

      <FlowAnswer v-if="askFlow.answer" :text="askFlow.answer" class="pt-4" />
      <AnswerActions
        v-if="askFlow.status === 'answered' && askFlow.answer"
        @send="(reply) => ask(reply, { followUp: true })"
      />

      <ApprovalCards
        v-if="askFlow.status === 'needs_you' && askFlow.approval"
        @ask-changes="askForChanges"
        @review="handOff"
      />

      <div
        v-if="askFlow.status === 'working' && askFlow.label"
        class="flex items-center gap-2 pt-4 text-base text-ink-gray-5"
      >
        <LucideLoaderCircle class="size-4 shrink-0 animate-spin" />
        <span class="truncate">{{ askFlow.label }}</span>
      </div>

      <div
        v-if="callout"
        class="mt-4 flex items-center gap-3 rounded-4 px-3 py-2.5 text-base"
        :class="callout.class"
      >
        <span class="flex-1">{{ callout.message }}</span>
        <Button
          variant="solid"
          :label="callout.action"
          @click="callout.perform"
        />
      </div>
    </div>

    <div
      class="flex items-center gap-2 border-t border-outline-gray-1 py-2 pe-2 ps-4"
    >
      <LucideCornerDownRight class="size-4 shrink-0 text-ink-gray-4" />
      <input
        ref="inputRef"
        v-model="followUp"
        :placeholder="
          changeFor ? __('Tell Flow what to change…') : __('Ask a follow-up…')
        "
        class="min-w-0 flex-1 border-none bg-transparent px-1 py-1.5 text-base text-ink-gray-8 placeholder-ink-gray-4 focus:outline-none focus:ring-0 focus-visible:outline-none focus-visible:ring-0"
        autocomplete="off"
        spellcheck="false"
        @keydown="onKeydown"
      />
      <Button
        v-if="askFlow.status === 'working'"
        :label="__('Stop')"
        @click="stop"
      />
    </div>
  </div>
</template>

<script setup>
import { Button, toast } from 'frappe-ui'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import LucideChevronDown from '~icons/lucide/chevron-down'
import LucideChevronUp from '~icons/lucide/chevron-up'
import LucideCornerDownRight from '~icons/lucide/corner-down-right'
import LucideLoaderCircle from '~icons/lucide/loader-circle'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideX from '~icons/lucide/x'
import {
  closeCommandPalette,
  commandPaletteQuery,
} from '@/composables/useCommandPalette'
import AnswerActions from './AnswerActions.vue'
import ApprovalCards from './ApprovalCards.vue'
import ChatHistory from './ChatHistory.vue'
import FlowAnswer from './FlowAnswer.vue'
import {
  answerApproval,
  ask,
  askFlow,
  hideAskFlow,
  newChat,
  openInFlow,
  retry,
  stop,
} from './askFlow'

const props = defineProps({
  surface: {
    type: String,
    default: 'palette',
    validator: (value) => ['palette', 'home'].includes(value),
  },
})

const emit = defineEmits(['new-chat'])

const inPalette = props.surface === 'palette'
const inputRef = ref(null)
const followUp = ref('')
const showEarlier = ref(false)
// the call whose changes the follow-up box is asking for
const changeFor = ref(null)

onMounted(() => nextTick(() => inputRef.value?.focus({ preventScroll: true })))
watch(
  () => askFlow.session,
  () => (showEarlier.value = false),
)
watch(
  () => askFlow.approval,
  (approval) => {
    if (!approval) changeFor.value = null
  },
)

const earlierLabel = computed(() => {
  const count = askFlow.earlier.length
  return count === 1
    ? __('1 earlier message')
    : __('{0} earlier messages', [count])
})

const contextLabel = computed(() => {
  const { doctype, name, title } = askFlow.context
  return `${doctype.replace('CRM ', '')}: ${title || name}`
})

const callout = computed(() => {
  // an approval the card cannot show: a tool's own form, a password, a sub-agent's
  if (askFlow.status === 'needs_you' && !askFlow.approval)
    return {
      class: 'bg-surface-amber-2 text-ink-amber-6',
      message: __('Flow is waiting for your approval'),
      action: __('Review'),
      perform: handOff,
    }
  if (askFlow.status === 'error')
    return {
      class: 'bg-surface-red-2 text-ink-red-6',
      message: askFlow.error,
      action: __('Try again'),
      perform: retry,
    }
  return null
})

function capitalize(text) {
  const trimmed = text.trim()
  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1)
}

function handOff() {
  if (openInFlow()) closeCommandPalette()
}

// In the palette a new question is typed in its search; on Home, in the empty box.
function startNewChat() {
  newChat()
  if (inPalette) backToSearch()
  emit('new-chat')
}

function askForChanges(callId) {
  changeFor.value = callId
  inputRef.value?.focus()
}

// From anywhere in the card: Esc first drops "Ask for changes", then goes back to search.
function onEscape(event) {
  if (changeFor.value) {
    event.preventDefault()
    event.stopPropagation()
    changeFor.value = null
  } else if (inPalette) {
    back(event)
  }
}

function onKeydown(event) {
  const mod = event.metaKey || event.ctrlKey
  if (inPalette && event.key === 'Backspace' && !followUp.value)
    return back(event)
  if (mod && event.key === 'Enter') return run(event, handOff)
  if (event.key === 'Enter' && !event.isComposing) run(event, sendFollowUp)
}

// Enter in the empty box presses the card's button: Review or Try again.
function sendFollowUp() {
  if (!followUp.value.trim()) return callout.value?.perform()
  if (changeFor.value) return sendChanges()
  if (askFlow.status === 'working') return
  ask(followUp.value, { followUp: true })
  followUp.value = ''
}

// What to change instead answers the call, as Flow's own "Ask for changes" does.
async function sendChanges() {
  const text = followUp.value.trim()
  try {
    await answerApproval(changeFor.value, text)
    followUp.value = ''
    changeFor.value = null
  } catch (error) {
    toast.error(
      error?.messages?.[0] || __('Could not send your answer to Flow'),
    )
  }
}

function back(event) {
  event.preventDefault()
  event.stopPropagation()
  backToSearch()
}

// A fresh search: the chat stays pinned above the results.
function backToSearch() {
  commandPaletteQuery.value = ''
  hideAskFlow()
}

function run(event, action) {
  event.preventDefault()
  action()
}
</script>
